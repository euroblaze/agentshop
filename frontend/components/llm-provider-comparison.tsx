import React, { useState, useEffect } from 'react';
import { LLMApiClient, LLMResponse } from '../services/llm-api-client';

interface ComparisonResult {
  provider: string;
  response?: LLMResponse;
  error?: string;
  loading: boolean;
}

interface ProviderComparisonProps {
  apiClient: LLMApiClient;
  onCostUpdate?: (totalCost: number) => void;
}

export const ProviderComparison: React.FC<ProviderComparisonProps> = ({
  apiClient,
  onCostUpdate
}) => {
  const [prompt, setPrompt] = useState('');
  const [selectedProviders, setSelectedProviders] = useState<string[]>([]);
  const [availableProviders, setAvailableProviders] = useState<string[]>([]);
  const [results, setResults] = useState<ComparisonResult[]>([]);
  const [isComparing, setIsComparing] = useState(false);
  const [totalCost, setTotalCost] = useState(0);

  useEffect(() => {
    loadProviders();
  }, []);

  useEffect(() => {
    if (onCostUpdate) {
      onCostUpdate(totalCost);
    }
  }, [totalCost, onCostUpdate]);

  const loadProviders = async () => {
    try {
      const providers = await apiClient.getProviders();
      setAvailableProviders(providers);
      setSelectedProviders(providers.slice(0, 2)); // Select first 2 by default
    } catch (error) {
      console.error('Failed to load providers:', error);
    }
  };

  const handleProviderToggle = (provider: string) => {
    setSelectedProviders(prev => 
      prev.includes(provider)
        ? prev.filter(p => p !== provider)
        : [...prev, provider]
    );
  };

  const handleCompare = async () => {
    if (!prompt.trim() || selectedProviders.length === 0 || isComparing) {
      return;
    }

    setIsComparing(true);
    setResults([]);

    // Initialize results with loading state
    const initialResults: ComparisonResult[] = selectedProviders.map(provider => ({
      provider,
      loading: true
    }));
    setResults(initialResults);

    try {
      const responses = await apiClient.compareProviders(prompt, selectedProviders);
      
      const finalResults: ComparisonResult[] = selectedProviders.map(provider => {
        const result = responses[provider];
        
        if ('error' in result) {
          return {
            provider,
            error: result.error,
            loading: false
          };
        } else {
          return {
            provider,
            response: result as LLMResponse,
            loading: false
          };
        }
      });

      setResults(finalResults);

      // Calculate total cost
      const cost = finalResults.reduce((sum, result) => {
        return sum + (result.response?.cost || 0);
      }, 0);
      setTotalCost(prev => prev + cost);

    } catch (error) {
      const errorResults: ComparisonResult[] = selectedProviders.map(provider => ({
        provider,
        error: error instanceof Error ? error.message : 'Unknown error',
        loading: false
      }));
      setResults(errorResults);
    } finally {
      setIsComparing(false);
    }
  };

  const clearResults = () => {
    setResults([]);
    setTotalCost(0);
  };

  const formatMetadata = (metadata?: Record<string, any>) => {
    if (!metadata) return null;
    
    return Object.entries(metadata).map(([key, value]) => (
      <div key={key} className="metadata-item">
        <strong>{key}:</strong> {JSON.stringify(value)}
      </div>
    ));
  };

  return (
    <div className="provider-comparison">
      <div className="comparison-header">
        <h3>LLM Provider Comparison</h3>
        <div className="cost-display">
          Total Cost: ${totalCost.toFixed(4)}
        </div>
      </div>

      <div className="prompt-section">
        <label htmlFor="comparison-prompt">Prompt:</label>
        <textarea
          id="comparison-prompt"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Enter your prompt to compare across providers..."
          rows={4}
          disabled={isComparing}
        />
      </div>

      <div className="provider-selection">
        <label>Select Providers to Compare:</label>
        <div className="provider-checkboxes">
          {availableProviders.map(provider => (
            <label key={provider} className="provider-checkbox">
              <input
                type="checkbox"
                checked={selectedProviders.includes(provider)}
                onChange={() => handleProviderToggle(provider)}
                disabled={isComparing}
              />
              {provider.charAt(0).toUpperCase() + provider.slice(1)}
            </label>
          ))}
        </div>
      </div>

      <div className="comparison-actions">
        <button
          onClick={handleCompare}
          disabled={!prompt.trim() || selectedProviders.length === 0 || isComparing}
          className="compare-button"
        >
          {isComparing ? 'Comparing...' : 'Compare Providers'}
        </button>
        <button onClick={clearResults} className="clear-button">
          Clear Results
        </button>
      </div>

      {results.length > 0 && (
        <div className="comparison-results">
          <h4>Comparison Results</h4>
          <div className="results-grid">
            {results.map(result => (
              <div key={result.provider} className="result-card">
                <div className="result-header">
                  <h5>{result.provider.charAt(0).toUpperCase() + result.provider.slice(1)}</h5>
                  {result.loading && <div className="loading-spinner">Loading...</div>}
                </div>

                {result.error && (
                  <div className="result-error">
                    <strong>Error:</strong> {result.error}
                  </div>
                )}

                {result.response && (
                  <div className="result-content">
                    <div className="response-text">
                      {result.response.content}
                    </div>
                    
                    <div className="response-stats">
                      <div className="stat">
                        <strong>Model:</strong> {result.response.model}
                      </div>
                      <div className="stat">
                        <strong>Tokens:</strong> {result.response.tokens_used}
                      </div>
                      <div className="stat">
                        <strong>Cost:</strong> ${result.response.cost.toFixed(4)}
                      </div>
                      {result.response.cached && (
                        <div className="stat cached">
                          <strong>Cached Response</strong>
                        </div>
                      )}
                    </div>

                    {result.response.metadata && (
                      <div className="response-metadata">
                        <strong>Metadata:</strong>
                        {formatMetadata(result.response.metadata)}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};