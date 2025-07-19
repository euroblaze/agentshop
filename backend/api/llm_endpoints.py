from flask import Blueprint, request, jsonify
from typing import Dict, Any
import asyncio
from ..services.llm import LLMService, LLMProvider
from ..middleware.rate_limiter import llm_rate_limit
from ..middleware.error_handler import ErrorHandler


llm_bp = Blueprint('llm', __name__, url_prefix='/api/llm')


# Global LLM service instance
llm_service = LLMService()


@llm_bp.route('/providers', methods=['GET'])
def get_providers():
    """Get list of available LLM providers"""
    try:
        providers = llm_service.get_available_providers()
        return jsonify({
            "success": True,
            "data": [provider.value for provider in providers],
            "message": "Providers retrieved successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Failed to get providers: {str(e)}"
        }), 500


@llm_bp.route('/models/<provider_name>', methods=['GET'])
def get_models(provider_name: str):
    """Get available models for a specific provider"""
    try:
        provider = LLMProvider(provider_name.lower())
        models = llm_service.get_available_models(provider)
        
        return jsonify({
            "success": True,
            "data": models,
            "message": f"Models for {provider_name} retrieved successfully"
        })
    except ValueError:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Unknown provider: {provider_name}"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Failed to get models: {str(e)}"
        }), 500


@llm_bp.route('/generate', methods=['POST'])
@llm_rate_limit(requests_per_minute=10)
def generate():
    """Generate text using an LLM provider"""
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({
                "success": False,
                "data": None,
                "message": "Prompt is required"
            }), 400
        
        prompt = data['prompt']
        provider_name = data.get('provider')
        model = data.get('model')
        
        # Optional parameters
        kwargs = {
            'temperature': data.get('temperature', 0.7),
            'max_tokens': data.get('max_tokens', 1000),
            'top_p': data.get('top_p', 1.0),
            'stream': data.get('stream', False),
            'context': data.get('context')
        }
        
        provider = None
        if provider_name:
            try:
                provider = LLMProvider(provider_name.lower())
            except ValueError:
                return jsonify({
                    "success": False,
                    "data": None,
                    "message": f"Unknown provider: {provider_name}"
                }), 400
        
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            response = loop.run_until_complete(
                llm_service.generate(prompt, provider, model, **kwargs)
            )
        finally:
            loop.close()
        
        return jsonify({
            "success": True,
            "data": {
                "content": response.content,
                "provider": response.provider.value,
                "model": response.model,
                "tokens_used": response.tokens_used,
                "cost": response.cost,
                "cached": response.cached,
                "metadata": response.metadata
            },
            "message": "Text generated successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Generation failed: {str(e)}"
        }), 500


@llm_bp.route('/generate/compare', methods=['POST'])
@llm_rate_limit(requests_per_minute=5)
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
        provider_names = data['providers']
        model = data.get('model')
        
        # Optional parameters
        kwargs = {
            'temperature': data.get('temperature', 0.7),
            'max_tokens': data.get('max_tokens', 1000),
            'top_p': data.get('top_p', 1.0),
            'context': data.get('context')
        }
        
        # Convert provider names to enum values
        providers = []
        for provider_name in provider_names:
            try:
                providers.append(LLMProvider(provider_name.lower()))
            except ValueError:
                return jsonify({
                    "success": False,
                    "data": None,
                    "message": f"Unknown provider: {provider_name}"
                }), 400
        
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(
                llm_service.compare_providers(prompt, providers, model, **kwargs)
            )
        finally:
            loop.close()
        
        # Format results
        formatted_results = {}
        for provider, response in results.items():
            if isinstance(response, Exception):
                formatted_results[provider.value] = {
                    "error": str(response)
                }
            else:
                formatted_results[provider.value] = {
                    "content": response.content,
                    "model": response.model,
                    "tokens_used": response.tokens_used,
                    "cost": response.cost,
                    "cached": response.cached,
                    "metadata": response.metadata
                }
        
        return jsonify({
            "success": True,
            "data": formatted_results,
            "message": "Provider comparison completed"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Comparison failed: {str(e)}"
        }), 500


@llm_bp.route('/cost/estimate', methods=['POST'])
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
        
        try:
            provider = LLMProvider(provider_name.lower())
        except ValueError:
            return jsonify({
                "success": False,
                "data": None,
                "message": f"Unknown provider: {provider_name}"
            }), 400
        
        # Optional parameters
        kwargs = {
            'temperature': data.get('temperature', 0.7),
            'max_tokens': data.get('max_tokens', 1000),
            'top_p': data.get('top_p', 1.0),
            'context': data.get('context')
        }
        
        cost = llm_service.estimate_cost(prompt, provider, model, **kwargs)
        
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


@llm_bp.route('/health', methods=['GET'])
def health_check():
    """Check health of all LLM providers"""
    try:
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            health_status = loop.run_until_complete(llm_service.health_check())
        finally:
            loop.close()
        
        # Format results
        formatted_status = {
            provider.value: status for provider, status in health_status.items()
        }
        
        return jsonify({
            "success": True,
            "data": formatted_status,
            "message": "Health check completed"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Health check failed: {str(e)}"
        }), 500