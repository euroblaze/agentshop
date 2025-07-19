from flask import Blueprint, request, jsonify
from ..config.llm_config import config_manager
from ..middleware.rate_limiter import rate_limit


llm_config_bp = Blueprint('llm_config', __name__, url_prefix='/api/llm/config')


@llm_config_bp.route('/', methods=['GET'])
def get_config():
    """Get current LLM configuration (without sensitive data)"""
    try:
        safe_config = config_manager.get_safe_config()
        return jsonify({
            "success": True,
            "data": safe_config,
            "message": "Configuration retrieved successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Failed to get configuration: {str(e)}"
        }), 500


@llm_config_bp.route('/validate', methods=['GET'])
def validate_config():
    """Validate current LLM configuration"""
    try:
        validation_result = config_manager.validate_config()
        return jsonify({
            "success": True,
            "data": validation_result,
            "message": "Configuration validation completed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Configuration validation failed: {str(e)}"
        }), 500


@llm_config_bp.route('/providers/<provider_name>/enable', methods=['POST'])
@rate_limit(requests_per_minute=10)
def enable_provider(provider_name: str):
    """Enable an LLM provider"""
    try:
        data = request.get_json()
        
        if not data or 'api_key' not in data:
            return jsonify({
                "success": False,
                "data": None,
                "message": "API key is required"
            }), 400
        
        api_key = data['api_key']
        
        # Extract additional configuration
        kwargs = {}
        for key in ['base_url', 'organization', 'default_model', 'max_tokens', 'temperature', 'rate_limit_rpm', 'cost_limit_daily']:
            if key in data:
                kwargs[key] = data[key]
        
        config_manager.enable_provider(provider_name, api_key, **kwargs)
        
        return jsonify({
            "success": True,
            "data": {"provider": provider_name, "enabled": True},
            "message": f"Provider {provider_name} enabled successfully"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Failed to enable provider: {str(e)}"
        }), 500


@llm_config_bp.route('/providers/<provider_name>/disable', methods=['POST'])
@rate_limit(requests_per_minute=10)
def disable_provider(provider_name: str):
    """Disable an LLM provider"""
    try:
        config_manager.disable_provider(provider_name)
        
        return jsonify({
            "success": True,
            "data": {"provider": provider_name, "enabled": False},
            "message": f"Provider {provider_name} disabled successfully"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Failed to disable provider: {str(e)}"
        }), 500


@llm_config_bp.route('/providers/<provider_name>', methods=['PUT'])
@rate_limit(requests_per_minute=10)
def update_provider_config(provider_name: str):
    """Update configuration for a specific provider"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "data": None,
                "message": "Configuration data is required"
            }), 400
        
        # Update provider configuration
        config_manager.update_provider_config(provider_name, **data)
        
        return jsonify({
            "success": True,
            "data": {"provider": provider_name},
            "message": f"Provider {provider_name} configuration updated successfully"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Failed to update provider configuration: {str(e)}"
        }), 500


@llm_config_bp.route('/default-provider', methods=['PUT'])
@rate_limit(requests_per_minute=10)
def set_default_provider():
    """Set the default LLM provider"""
    try:
        data = request.get_json()
        
        if not data or 'provider' not in data:
            return jsonify({
                "success": False,
                "data": None,
                "message": "Provider name is required"
            }), 400
        
        provider_name = data['provider']
        
        # Check if provider is enabled
        if not config_manager.is_provider_enabled(provider_name):
            return jsonify({
                "success": False,
                "data": None,
                "message": f"Provider {provider_name} is not enabled"
            }), 400
        
        config_manager.config.default_provider = provider_name
        
        return jsonify({
            "success": True,
            "data": {"default_provider": provider_name},
            "message": f"Default provider set to {provider_name}"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Failed to set default provider: {str(e)}"
        }), 500


@llm_config_bp.route('/settings', methods=['PUT'])
@rate_limit(requests_per_minute=5)
def update_settings():
    """Update general LLM settings"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "data": None,
                "message": "Settings data is required"
            }), 400
        
        # Update general settings
        if 'cache_ttl' in data:
            config_manager.config.cache_ttl = int(data['cache_ttl'])
        
        if 'enable_caching' in data:
            config_manager.config.enable_caching = bool(data['enable_caching'])
        
        if 'enable_rate_limiting' in data:
            config_manager.config.enable_rate_limiting = bool(data['enable_rate_limiting'])
        
        if 'log_requests' in data:
            config_manager.config.log_requests = bool(data['log_requests'])
        
        return jsonify({
            "success": True,
            "data": config_manager.get_safe_config(),
            "message": "Settings updated successfully"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "message": f"Failed to update settings: {str(e)}"
        }), 500