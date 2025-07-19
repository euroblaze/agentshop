from flask import Blueprint, request, jsonify
import asyncio
from ..services.llm_orm_service import llm_orm_service
from ..middleware.rate_limiter import llm_rate_limit


llm_chat_bp = Blueprint('llm_chat', __name__, url_prefix='/api/llm/chat')


@llm_chat_bp.route('/message', methods=['POST'])
@llm_rate_limit(requests_per_minute=15)
def send_message():
    """Send a message in a chat conversation"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data or 'session_id' not in data:
            return jsonify({
                "success": False,
                "data": None,
                "message": "Message and session_id are required"
            }), 400
        
        message = data['message']
        session_id = data['session_id']
        user_id = data.get('user_id')
        provider = data.get('provider')
        model = data.get('model')
        
        # Optional parameters
        kwargs = {
            'temperature': data.get('temperature', 0.7),
            'max_tokens': data.get('max_tokens', 1000),
            'top_p': data.get('top_p', 1.0),
            'context': data.get('context'),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent')
        }
        
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                llm_orm_service.chat_conversation(
                    message=message,
                    session_id=session_id,
                    user_id=user_id,
                    provider=provider,
                    model=model,
                    **kwargs
                )
            )
        finally:
            loop.close()
        
        return jsonify({
            "success": True,
            "data": result,
            "message": "Message sent successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Failed to send message: {str(e)}"
        }), 500


@llm_chat_bp.route('/history/<session_id>', methods=['GET'])
def get_conversation_history(session_id: str):
    """Get conversation history for a session"""
    try:
        limit = request.args.get('limit', type=int)
        
        result = llm_orm_service.get_conversation_history(session_id, limit)
        
        return jsonify({
            "success": True,
            "data": result,
            "message": "Conversation history retrieved successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Failed to get conversation history: {str(e)}"
        }), 500


@llm_chat_bp.route('/conversations/user/<int:user_id>', methods=['GET'])
def get_user_conversations(user_id: int):
    """Get all conversations for a user"""
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        conversations = llm_orm_service.get_user_conversations(user_id, active_only)
        
        return jsonify({
            "success": True,
            "data": conversations,
            "message": "User conversations retrieved successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Failed to get user conversations: {str(e)}"
        }), 500


@llm_chat_bp.route('/compare', methods=['POST'])
@llm_rate_limit(requests_per_minute=3)
def compare_providers():
    """Compare responses from multiple providers"""
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data or 'providers' not in data:
            return jsonify({
                "success": False,
                "data": None,
                "message": "Prompt and providers list are required"
            }), 400
        
        prompt = data['prompt']
        providers = data['providers']
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        
        # Optional parameters
        kwargs = {
            'temperature': data.get('temperature', 0.7),
            'max_tokens': data.get('max_tokens', 1000),
            'top_p': data.get('top_p', 1.0),
            'context': data.get('context'),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent')
        }
        
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                llm_orm_service.compare_providers(
                    prompt=prompt,
                    providers=providers,
                    user_id=user_id,
                    session_id=session_id,
                    **kwargs
                )
            )
        finally:
            loop.close()
        
        return jsonify({
            "success": True,
            "data": result,
            "message": "Provider comparison completed"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Comparison failed: {str(e)}"
        }), 500