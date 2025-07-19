#!/usr/bin/env python3
"""
Test script for Groq integration
Run this to verify Groq provider is working correctly
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.llm import LLMProvider, LLMRequest
from services.llm.groq_provider import GroqProvider

load_dotenv()


async def test_groq_provider():
    """Test the Groq provider implementation"""
    print("🧪 Testing Groq Provider Integration")
    print("=" * 50)
    
    # Check if API key is available
    api_key = os.getenv('LLM_GROQ_API_KEY')
    if not api_key:
        print("[ERROR] LLM_GROQ_API_KEY not found in environment")
        print("   Please set your Groq API key in .env file")
        return False
    
    try:
        # Initialize provider
        print("[SETUP] Initializing Groq provider...")
        provider = GroqProvider(api_key=api_key)
        
        # Validate configuration
        print("[OK] Validating configuration...")
        if not provider.validate_config():
            print("[ERROR] Configuration validation failed")
            return False
        
        # Test available models
        print("[INFO] Getting available models...")
        models = provider.get_available_models()
        print(f"   Available models: {len(models)}")
        for model in models[:5]:  # Show first 5
            print(f"   - {model}")
        if len(models) > 5:
            print(f"   ... and {len(models) - 5} more")
        
        # Test cost estimation
        print("\n[COST] Testing cost estimation...")
        test_request = LLMRequest(
            prompt="Hello, how are you?",
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=100
        )
        
        estimated_cost = provider.estimate_cost(test_request)
        print(f"   Estimated cost for test request: ${estimated_cost:.8f}")
        
        # Test actual generation
        print("\n[TEST] Testing text generation...")
        print("   Prompt: 'Write a short greeting in one sentence.'")
        
        generation_request = LLMRequest(
            prompt="Write a short greeting in one sentence.",
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=50
        )
        
        response = await provider.generate(generation_request)
        
        print(f"   [OK] Generation successful!")
        print(f"   Response: {response.content}")
        print(f"   Provider: {response.provider.value}")
        print(f"   Model: {response.model}")
        print(f"   Tokens used: {response.tokens_used}")
        print(f"   Cost: ${response.cost:.8f}")
        print(f"   Cached: {response.cached}")
        
        if response.metadata:
            print(f"   Metadata: {response.metadata}")
        
        # Test with conversation context
        print("\n[CHAT] Testing with conversation context...")
        context_request = LLMRequest(
            prompt="What's the weather like?",
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=50,
            context={
                "system_prompt": "You are a helpful assistant.",
                "conversation_history": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there! How can I help you today?"}
                ]
            }
        )
        
        context_response = await provider.generate(context_request)
        print(f"   [OK] Context generation successful!")
        print(f"   Response: {context_response.content}")
        print(f"   Cost: ${context_response.cost:.8f}")
        
        print("\n🎉 All Groq tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_groq_in_llm_service():
    """Test Groq integration within the LLM service"""
    print("\n[SETUP] Testing Groq in LLM Service")
    print("=" * 50)
    
    try:
        from services.llm import LLMService
        
        # Initialize service
        llm_service = LLMService()
        
        # Register Groq provider
        api_key = os.getenv('LLM_GROQ_API_KEY')
        if not api_key:
            print("[ERROR] Cannot test LLM service without API key")
            return False
        
        print("[SETUP] Registering Groq provider in LLM service...")
        llm_service.register_provider(
            LLMProvider.GROQ,
            api_key=api_key,
            config={'default_model': 'llama3-8b-8192'}
        )
        
        # Test generation
        print("[TEST] Testing generation through LLM service...")
        response = await llm_service.generate(
            prompt="Say hello in a creative way.",
            provider=LLMProvider.GROQ,
            model="llama3-8b-8192",
            temperature=0.8,
            max_tokens=30
        )
        
        print(f"   [OK] Service generation successful!")
        print(f"   Response: {response.content}")
        print(f"   Provider: {response.provider.value}")
        print(f"   Cost: ${response.cost:.8f}")
        
        # Test provider comparison
        print("\n[COMPARE] Testing provider comparison...")
        available_providers = llm_service.get_available_providers()
        print(f"   Available providers: {[p.value for p in available_providers]}")
        
        if len(available_providers) > 1:
            comparison_results = await llm_service.compare_providers(
                prompt="Count to three.",
                providers=available_providers[:2],  # Test with first 2 providers
                max_tokens=20
            )
            
            print(f"   [OK] Comparison successful!")
            for provider, result in comparison_results.items():
                if isinstance(result, Exception):
                    print(f"   {provider.value}: Error - {result}")
                else:
                    print(f"   {provider.value}: {result.content[:50]}...")
        
        print("🎉 LLM Service integration tests passed!")
        return True
        
    except Exception as e:
        print(f"[ERROR] LLM Service test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("🧪 Groq Integration Test Suite")
    print("=" * 50)
    
    # Test basic provider
    provider_test = await test_groq_provider()
    
    # Test in LLM service
    service_test = await test_groq_in_llm_service()
    
    print("\n" + "=" * 50)
    print("[RESULTS] Test Results Summary")
    print("=" * 50)
    print(f"Provider Test: {'[OK] PASSED' if provider_test else '[ERROR] FAILED'}")
    print(f"Service Test:  {'[OK] PASSED' if service_test else '[ERROR] FAILED'}")
    
    if provider_test and service_test:
        print("\n🎉 All tests passed! Groq integration is working correctly.")
        print("\n[TIP] Next steps:")
        print("   1. Set LLM_GROQ_ENABLED=true in your .env file")
        print("   2. Start the backend server")
        print("   3. Test via API endpoints")
    else:
        print("\n[ERROR] Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())