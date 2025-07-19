import asyncio
import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..services.llm import LLMService, LLMProvider, LLMRequest as LLMServiceRequest, LLMResponse as LLMServiceResponse
from ..repositories.llm_repository import (
    LLMRequestRepository, LLMResponseRepository, LLMConversationRepository,
    LLMConversationMessageRepository, LLMUsageStatsRepository, LLMProviderStatusRepository
)
from ..models.llm_models import LLMRequest, LLMResponse, LLMConversation
from ..config.llm_config import config_manager


class LLMORMService:
    """Service that integrates LLM providers with ORM layer"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.request_repo = LLMRequestRepository()
        self.response_repo = LLMResponseRepository()
        self.conversation_repo = LLMConversationRepository()
        self.message_repo = LLMConversationMessageRepository()
        self.usage_repo = LLMUsageStatsRepository()
        self.status_repo = LLMProviderStatusRepository()
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize LLM providers from configuration"""
        for provider_name in config_manager.get_enabled_providers():
            provider_config = config_manager.get_provider_config(provider_name)
            if provider_config and provider_config.enabled:
                try:
                    provider_enum = LLMProvider(provider_name)
                    self.llm_service.register_provider(
                        provider_enum,
                        api_key=provider_config.api_key,
                        config={
                            'base_url': provider_config.base_url,
                            'organization': provider_config.organization,
                            'default_model': provider_config.default_model
                        },
                        set_as_default=(provider_name == config_manager.config.default_provider)
                    )
                except Exception as e:
                    print(f"Failed to initialize provider {provider_name}: {e}")
    
    async def generate_text(
        self,
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        request_type: str = 'generation',
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text and log to database"""
        
        # Create database request record
        db_request = self.request_repo.create_request(
            provider=provider or config_manager.config.default_provider,
            model=model or 'default',
            prompt=prompt,
            request_type=request_type,
            user_id=user_id,
            session_id=session_id,
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 1000),
            top_p=kwargs.get('top_p', 1.0),
            stream=kwargs.get('stream', False),
            context=kwargs.get('context'),
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent')
        )
        
        try:
            # Update status to processing
            self.request_repo.update_status(db_request.id, 'processing')
            
            # Convert provider string to enum
            provider_enum = None
            if provider:
                try:
                    provider_enum = LLMProvider(provider.lower())
                except ValueError:
                    raise ValueError(f"Unknown provider: {provider}")
            
            # Record start time
            start_time = time.time()
            
            # Generate response using LLM service
            llm_response = await self.llm_service.generate(
                prompt=prompt,
                provider=provider_enum,
                model=model,
                **kwargs
            )
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Create database response record
            db_response = self.response_repo.create_response(
                request_id=db_request.id,
                content=llm_response.content,
                tokens_used=llm_response.tokens_used,
                cost=llm_response.cost,
                cached=llm_response.cached,
                processing_time_ms=processing_time_ms,
                metadata=llm_response.metadata,
                finish_reason=llm_response.metadata.get('finish_reason') if llm_response.metadata else None
            )
            
            # Update request status to completed
            self.request_repo.update_status(
                db_request.id, 
                'completed',
                actual_cost=llm_response.cost
            )
            
            # Record usage statistics
            self.usage_repo.record_usage(
                provider=llm_response.provider.value,
                model=llm_response.model,
                tokens_used=llm_response.tokens_used,
                cost=llm_response.cost,
                success=True,
                response_time_ms=processing_time_ms,
                cached=llm_response.cached
            )
            
            # Update provider daily cost
            self.status_repo.increment_daily_cost(
                llm_response.provider.value, 
                llm_response.cost
            )
            
            return {
                'success': True,
                'request_id': db_request.id,
                'response_id': db_response.id,
                'content': llm_response.content,
                'provider': llm_response.provider.value,
                'model': llm_response.model,
                'tokens_used': llm_response.tokens_used,
                'cost': llm_response.cost,
                'cached': llm_response.cached,
                'processing_time_ms': processing_time_ms,
                'metadata': llm_response.metadata
            }
            
        except Exception as e:
            # Update request status to failed
            self.request_repo.update_status(db_request.id, 'failed')
            
            # Record failed usage
            self.usage_repo.record_usage(
                provider=provider or config_manager.config.default_provider,
                model=model or 'unknown',
                tokens_used=0,
                cost=0.0,
                success=False
            )
            
            raise e
    
    async def chat_conversation(
        self,
        message: str,
        session_id: str,
        user_id: Optional[int] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Handle chat conversation with context"""
        
        # Get or create conversation
        conversation = self.conversation_repo.get_by_session_id(session_id)
        if not conversation:
            conversation = self.conversation_repo.create_conversation(
                session_id=session_id,
                user_id=user_id,
                title=message[:50] + "..." if len(message) > 50 else message,
                default_provider=provider,
                default_model=model
            )
        
        # Add user message to conversation
        user_message = self.message_repo.add_message(
            conversation_id=conversation.id,
            role='user',
            content=message
        )
        
        # Get conversation history for context
        messages = self.message_repo.get_conversation_messages(conversation.id)
        conversation_history = [
            {'role': msg.role, 'content': msg.content}
            for msg in messages[:-1]  # Exclude the current user message
        ]
        
        # Add conversation context
        context = kwargs.get('context', {})
        context['conversation_history'] = conversation_history
        
        # Use conversation's default provider/model if not specified
        effective_provider = provider or conversation.default_provider
        effective_model = model or conversation.default_model
        
        try:
            # Generate response
            result = await self.generate_text(
                prompt=message,
                provider=effective_provider,
                model=effective_model,
                user_id=user_id,
                session_id=session_id,
                request_type='chat',
                context=context,
                **kwargs
            )
            
            # Add assistant message to conversation
            assistant_message = self.message_repo.add_message(
                conversation_id=conversation.id,
                role='assistant',
                content=result['content'],
                llm_request_id=result['request_id'],
                tokens_used=result['tokens_used'],
                cost=result['cost'],
                provider=result['provider'],
                model=result['model']
            )
            
            # Update conversation statistics
            self.conversation_repo.increment_message_count(conversation.id)
            self.conversation_repo.add_cost(conversation.id, result['cost'])
            
            return {
                **result,
                'conversation_id': conversation.id,
                'user_message_id': user_message.id,
                'assistant_message_id': assistant_message.id,
                'message_count': conversation.message_count + 2  # +2 for user and assistant messages
            }
            
        except Exception as e:
            # Still increment message count for user message
            self.conversation_repo.increment_message_count(conversation.id)
            raise e
    
    async def compare_providers(
        self,
        prompt: str,
        providers: List[str],
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Compare responses from multiple providers"""
        
        session_id = session_id or str(uuid.uuid4())
        results = {}
        total_cost = 0.0
        
        for provider in providers:
            try:
                result = await self.generate_text(
                    prompt=prompt,
                    provider=provider,
                    user_id=user_id,
                    session_id=session_id,
                    request_type='comparison',
                    **kwargs
                )
                results[provider] = {
                    'success': True,
                    'content': result['content'],
                    'model': result['model'],
                    'tokens_used': result['tokens_used'],
                    'cost': result['cost'],
                    'cached': result['cached'],
                    'processing_time_ms': result['processing_time_ms'],
                    'request_id': result['request_id'],
                    'response_id': result['response_id']
                }
                total_cost += result['cost']
                
            except Exception as e:
                results[provider] = {
                    'success': False,
                    'error': str(e)
                }
        
        return {
            'session_id': session_id,
            'results': results,
            'total_cost': total_cost,
            'providers_count': len(providers),
            'successful_count': sum(1 for r in results.values() if r.get('success', False))
        }
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get conversation history"""
        conversation = self.conversation_repo.get_by_session_id(session_id)
        if not conversation:
            return {'conversation': None, 'messages': []}
        
        messages = self.message_repo.get_conversation_messages(conversation.id, limit)
        
        return {
            'conversation': conversation.to_dict(),
            'messages': [msg.to_dict() for msg in messages]
        }
    
    def get_user_conversations(
        self,
        user_id: int,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get user's conversations"""
        conversations = self.conversation_repo.get_user_conversations(user_id, active_only)
        return [conv.to_dict() for conv in conversations]
    
    def get_usage_statistics(
        self,
        period_type: str = 'day',
        days: int = 7,
        provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get usage statistics"""
        stats = self.usage_repo.get_usage_summary(period_type, days, provider)
        return [stat.to_dict() for stat in stats]
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers"""
        health_results = await self.llm_service.health_check()
        
        # Update provider status in database
        for provider, is_healthy in health_results.items():
            self.status_repo.update_provider_status(
                provider.value,
                is_healthy=is_healthy
            )
        
        return {
            provider.value: is_healthy 
            for provider, is_healthy in health_results.items()
        }
    
    def get_provider_status(self) -> List[Dict[str, Any]]:
        """Get status of all providers"""
        statuses = self.status_repo.get_all_provider_status()
        return [status.to_dict() for status in statuses]


# Global LLM ORM service instance
llm_orm_service = LLMORMService()