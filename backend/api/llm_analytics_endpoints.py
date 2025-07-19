from flask import Blueprint, request, jsonify
import asyncio
from ..services.llm_orm_service import llm_orm_service
from ..middleware.rate_limiter import rate_limit


llm_analytics_bp = Blueprint('llm_analytics', __name__, url_prefix='/api/llm/analytics')


@llm_analytics_bp.route('/usage', methods=['GET'])
@rate_limit(requests_per_minute=30)
def get_usage_statistics():
    """Get LLM usage statistics"""
    try:
        period_type = request.args.get('period_type', 'day')
        days = request.args.get('days', 7, type=int)
        provider = request.args.get('provider')
        
        if period_type not in ['hour', 'day', 'month']:
            return jsonify({
                "success": False,
                "data": None,
                "message": "Invalid period_type. Must be 'hour', 'day', or 'month'"
            }), 400
        
        stats = llm_orm_service.get_usage_statistics(period_type, days, provider)
        
        return jsonify({
            "success": True,
            "data": stats,
            "message": "Usage statistics retrieved successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Failed to get usage statistics: {str(e)}"
        }), 500


@llm_analytics_bp.route('/providers/status', methods=['GET'])
def get_provider_status():
    """Get status of all LLM providers"""
    try:
        statuses = llm_orm_service.get_provider_status()
        
        return jsonify({
            "success": True,
            "data": statuses,
            "message": "Provider statuses retrieved successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Failed to get provider status: {str(e)}"
        }), 500


@llm_analytics_bp.route('/health', methods=['GET'])
def health_check():
    """Perform health check on all LLM providers"""
    try:
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            health_status = loop.run_until_complete(llm_orm_service.health_check())
        finally:
            loop.close()
        
        return jsonify({
            "success": True,
            "data": health_status,
            "message": "Health check completed"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Health check failed: {str(e)}"
        }), 500


@llm_analytics_bp.route('/cost/estimate', methods=['POST'])
@rate_limit(requests_per_minute=60)
def estimate_cost():
    """Estimate cost for an LLM request"""
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data or 'provider' not in data:
            return jsonify({
                "success": False,
                "data": None,
                "message": "Prompt and provider are required"
            }), 400
        
        prompt = data['prompt']
        provider_name = data['provider']
        model = data.get('model')
        
        # Optional parameters
        kwargs = {
            'temperature': data.get('temperature', 0.7),
            'max_tokens': data.get('max_tokens', 1000),
            'top_p': data.get('top_p', 1.0),
            'context': data.get('context')
        }
        
        try:
            from ..services.llm import LLMProvider
            provider = LLMProvider(provider_name.lower())
        except ValueError:
            return jsonify({
                "success": False,
                "data": None,
                "message": f"Unknown provider: {provider_name}"
            }), 400
        
        cost = llm_orm_service.llm_service.estimate_cost(prompt, provider, model, **kwargs)
        
        return jsonify({
            "success": True,
            "data": {
                "estimated_cost": cost,
                "provider": provider_name,
                "model": model
            },
            "message": "Cost estimated successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Cost estimation failed: {str(e)}"
        }), 500


@llm_analytics_bp.route('/requests/<int:request_id>', methods=['GET'])
def get_request_details(request_id: int):
    """Get details of a specific LLM request"""
    try:
        request_obj = llm_orm_service.request_repo.get_by_id(request_id)
        if not request_obj:
            return jsonify({
                "success": False,
                "data": None,
                "message": "Request not found"
            }), 404
        
        response_obj = llm_orm_service.response_repo.get_by_request(request_id)
        
        result = {
            "request": request_obj.to_dict(),
            "response": response_obj.to_dict() if response_obj else None
        }
        
        return jsonify({
            "success": True,
            "data": result,
            "message": "Request details retrieved successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Failed to get request details: {str(e)}"
        }), 500


@llm_analytics_bp.route('/requests/user/<int:user_id>', methods=['GET'])
def get_user_requests(user_id: int):
    """Get LLM requests for a specific user"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        requests = llm_orm_service.request_repo.get_user_requests(user_id, limit, offset)
        
        return jsonify({
            "success": True,
            "data": [req.to_dict() for req in requests],
            "message": "User requests retrieved successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Failed to get user requests: {str(e)}"
        }), 500