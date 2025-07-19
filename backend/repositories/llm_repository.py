from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from sqlalchemy.orm import joinedload
from .base_repository import BaseRepository
from ..models.llm_models import (
    LLMRequest, LLMResponse, LLMConversation, 
    LLMConversationMessage, LLMUsageStats, LLMProviderStatus
)


class LLMRequestRepository(BaseRepository[LLMRequest]):
    """Repository for LLM requests"""
    
    def __init__(self):
        super().__init__(LLMRequest)
    
    def create_request(
        self,
        provider: str,
        model: str,
        prompt: str,
        request_type: str = 'generation',
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> LLMRequest:
        """Create a new LLM request"""
        return self.create(
            provider=provider,
            model=model,
            prompt=prompt,
            request_type=request_type,
            user_id=user_id,
            session_id=session_id,
            **kwargs
        )
    
    def get_by_session(self, session_id: str) -> List[LLMRequest]:
        """Get all requests for a session"""
        return self.find_by(session_id=session_id)
    
    def get_pending_requests(self) -> List[LLMRequest]:
        """Get all pending requests"""
        return self.find_by(status='pending')
    
    def update_status(self, request_id: int, status: str, **kwargs) -> Optional[LLMRequest]:
        """Update request status"""
        update_data = {'status': status}
        
        if status == 'processing':
            update_data['started_at'] = datetime.utcnow()
        elif status in ['completed', 'failed']:
            update_data['completed_at'] = datetime.utcnow()
        
        update_data.update(kwargs)
        return self.update(request_id, **update_data)
    
    def get_user_requests(
        self, 
        user_id: int, 
        limit: Optional[int] = None, 
        offset: int = 0
    ) -> List[LLMRequest]:
        """Get requests for a specific user"""
        session = self.get_session()
        try:
            query = session.query(LLMRequest).filter(LLMRequest.user_id == user_id)
            query = query.order_by(desc(LLMRequest.created_at))
            if limit:
                query = query.limit(limit)
            query = query.offset(offset)
            return query.all()
        finally:
            session.close()
    
    def get_requests_with_responses(self, **kwargs) -> List[LLMRequest]:
        """Get requests with their responses"""
        session = self.get_session()
        try:
            query = session.query(LLMRequest).options(joinedload(LLMRequest.response))
            for key, value in kwargs.items():
                if hasattr(LLMRequest, key):
                    query = query.filter(getattr(LLMRequest, key) == value)
            return query.all()
        finally:
            session.close()


class LLMResponseRepository(BaseRepository[LLMResponse]):
    """Repository for LLM responses"""
    
    def __init__(self):
        super().__init__(LLMResponse)
    
    def create_response(
        self,
        request_id: int,
        content: str,
        tokens_used: int = 0,
        cost: float = 0.0,
        **kwargs
    ) -> LLMResponse:
        """Create a new LLM response"""
        return self.create(
            request_id=request_id,
            content=content,
            tokens_used=tokens_used,
            cost=cost,
            response_length=len(content),
            **kwargs
        )
    
    def get_by_request(self, request_id: int) -> Optional[LLMResponse]:
        """Get response for a specific request"""
        return self.find_one_by(request_id=request_id)


class LLMConversationRepository(BaseRepository[LLMConversation]):
    """Repository for LLM conversations"""
    
    def __init__(self):
        super().__init__(LLMConversation)
    
    def create_conversation(
        self,
        session_id: str,
        user_id: Optional[int] = None,
        title: Optional[str] = None,
        **kwargs
    ) -> LLMConversation:
        """Create a new conversation"""
        return self.create(
            session_id=session_id,
            user_id=user_id,
            title=title,
            **kwargs
        )
    
    def get_by_session_id(self, session_id: str) -> Optional[LLMConversation]:
        """Get conversation by session ID"""
        return self.find_one_by(session_id=session_id)
    
    def get_user_conversations(
        self, 
        user_id: int, 
        active_only: bool = True
    ) -> List[LLMConversation]:
        """Get conversations for a user"""
        criteria = {'user_id': user_id}
        if active_only:
            criteria['is_active'] = True
        return self.find_by(**criteria)
    
    def update_activity(self, conversation_id: int) -> Optional[LLMConversation]:
        """Update last activity timestamp"""
        return self.update(conversation_id, last_activity=datetime.utcnow())
    
    def increment_message_count(self, conversation_id: int) -> Optional[LLMConversation]:
        """Increment message count"""
        session = self.get_session()
        try:
            conversation = session.query(LLMConversation).filter(
                LLMConversation.id == conversation_id
            ).first()
            if conversation:
                conversation.message_count += 1
                conversation.last_activity = datetime.utcnow()
                session.commit()
                session.refresh(conversation)
                return conversation
            return None
        finally:
            session.close()
    
    def add_cost(self, conversation_id: int, cost: float) -> Optional[LLMConversation]:
        """Add cost to conversation total"""
        session = self.get_session()
        try:
            conversation = session.query(LLMConversation).filter(
                LLMConversation.id == conversation_id
            ).first()
            if conversation:
                conversation.total_cost += cost
                session.commit()
                session.refresh(conversation)
                return conversation
            return None
        finally:
            session.close()


class LLMConversationMessageRepository(BaseRepository[LLMConversationMessage]):
    """Repository for conversation messages"""
    
    def __init__(self):
        super().__init__(LLMConversationMessage)
    
    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        **kwargs
    ) -> LLMConversationMessage:
        """Add a message to a conversation"""
        # Get the next message order
        session = self.get_session()
        try:
            max_order = session.query(func.max(LLMConversationMessage.message_order)).filter(
                LLMConversationMessage.conversation_id == conversation_id
            ).scalar() or 0
            
            return self.create(
                conversation_id=conversation_id,
                role=role,
                content=content,
                message_order=max_order + 1,
                **kwargs
            )
        finally:
            session.close()
    
    def get_conversation_messages(
        self, 
        conversation_id: int, 
        limit: Optional[int] = None
    ) -> List[LLMConversationMessage]:
        """Get messages for a conversation"""
        session = self.get_session()
        try:
            query = session.query(LLMConversationMessage).filter(
                LLMConversationMessage.conversation_id == conversation_id
            ).order_by(LLMConversationMessage.message_order)
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        finally:
            session.close()


class LLMUsageStatsRepository(BaseRepository[LLMUsageStats]):
    """Repository for usage statistics"""
    
    def __init__(self):
        super().__init__(LLMUsageStats)
    
    def record_usage(
        self,
        provider: str,
        model: str,
        tokens_used: int,
        cost: float,
        success: bool = True,
        response_time_ms: int = 0,
        cached: bool = False
    ):
        """Record usage statistics"""
        now = datetime.utcnow()
        
        # Record for different periods
        for period_type, date_truncated in [
            ('hour', now.replace(minute=0, second=0, microsecond=0)),
            ('day', now.replace(hour=0, minute=0, second=0, microsecond=0)),
        ]:
            self._update_or_create_stats(
                date_truncated, period_type, provider, model,
                tokens_used, cost, success, response_time_ms, cached
            )
    
    def _update_or_create_stats(
        self,
        date: datetime,
        period_type: str,
        provider: str,
        model: str,
        tokens_used: int,
        cost: float,
        success: bool,
        response_time_ms: int,
        cached: bool
    ):
        """Update or create statistics record"""
        session = self.get_session()
        try:
            stats = session.query(LLMUsageStats).filter(
                LLMUsageStats.date == date,
                LLMUsageStats.period_type == period_type,
                LLMUsageStats.provider == provider,
                LLMUsageStats.model == model
            ).first()
            
            if not stats:
                stats = LLMUsageStats(
                    date=date,
                    period_type=period_type,
                    provider=provider,
                    model=model
                )
                session.add(stats)
            
            # Update counters
            stats.request_count += 1
            if success:
                stats.successful_requests += 1
            else:
                stats.failed_requests += 1
            
            stats.total_tokens += tokens_used
            stats.total_cost += cost
            
            # Update averages
            if stats.request_count > 0:
                stats.average_cost_per_request = stats.total_cost / stats.request_count
                
                # Update response time average
                old_avg = stats.average_response_time_ms
                new_count = stats.request_count
                stats.average_response_time_ms = int(
                    (old_avg * (new_count - 1) + response_time_ms) / new_count
                )
            
            session.commit()
            
        finally:
            session.close()
    
    def get_usage_summary(
        self,
        period_type: str = 'day',
        days: int = 7,
        provider: Optional[str] = None
    ) -> List[LLMUsageStats]:
        """Get usage summary for a period"""
        session = self.get_session()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = session.query(LLMUsageStats).filter(
                LLMUsageStats.period_type == period_type,
                LLMUsageStats.date >= start_date
            )
            
            if provider:
                query = query.filter(LLMUsageStats.provider == provider)
            
            return query.order_by(desc(LLMUsageStats.date)).all()
        finally:
            session.close()


class LLMProviderStatusRepository(BaseRepository[LLMProviderStatus]):
    """Repository for provider status"""
    
    def __init__(self):
        super().__init__(LLMProviderStatus)
    
    def update_provider_status(
        self,
        provider: str,
        is_healthy: bool,
        **kwargs
    ) -> LLMProviderStatus:
        """Update provider status"""
        session = self.get_session()
        try:
            status = session.query(LLMProviderStatus).filter(
                LLMProviderStatus.provider == provider
            ).first()
            
            if not status:
                status = LLMProviderStatus(provider=provider)
                session.add(status)
            
            status.is_healthy = is_healthy
            status.last_health_check = datetime.utcnow()
            
            for key, value in kwargs.items():
                if hasattr(status, key):
                    setattr(status, key, value)
            
            session.commit()
            session.refresh(status)
            return status
            
        finally:
            session.close()
    
    def get_all_provider_status(self) -> List[LLMProviderStatus]:
        """Get status for all providers"""
        return self.get_all()
    
    def increment_daily_cost(self, provider: str, cost: float) -> Optional[LLMProviderStatus]:
        """Increment daily cost for a provider"""
        session = self.get_session()
        try:
            status = session.query(LLMProviderStatus).filter(
                LLMProviderStatus.provider == provider
            ).first()
            
            if status:
                status.current_daily_cost += cost
                session.commit()
                session.refresh(status)
                return status
            return None
        finally:
            session.close()