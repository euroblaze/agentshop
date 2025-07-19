export interface LLMRequest {
  prompt: string;
  provider?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  stream?: boolean;
  context?: Record<string, any>;
}

export interface LLMResponse {
  content: string;
  provider: string;
  model: string;
  tokens_used: number;
  cost: number;
  cached: boolean;
  metadata?: Record<string, any>;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
  errors?: string[];
}

export class LLMApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = '/api/llm') {
    this.baseUrl = baseUrl;
  }

  async getProviders(): Promise<string[]> {
    const response = await this.makeRequest<string[]>('/providers');
    return response.data;
  }

  async getModels(provider: string): Promise<string[]> {
    const response = await this.makeRequest<string[]>(`/models/${provider}`);
    return response.data;
  }

  async generate(request: LLMRequest): Promise<LLMResponse> {
    const response = await this.makeRequest<LLMResponse>('/generate', {
      method: 'POST',
      body: JSON.stringify(request)
    });
    return response.data;
  }

  async compareProviders(
    prompt: string,
    providers: string[],
    options?: Partial<LLMRequest>
  ): Promise<Record<string, LLMResponse | { error: string }>> {
    const request = {
      prompt,
      providers,
      ...options
    };

    const response = await this.makeRequest<Record<string, LLMResponse | { error: string }>>(
      '/generate/compare',
      {
        method: 'POST',
        body: JSON.stringify(request)
      }
    );
    return response.data;
  }

  async estimateCost(
    prompt: string,
    provider: string,
    options?: Partial<LLMRequest>
  ): Promise<{ estimated_cost: number; provider: string; model?: string }> {
    const request = {
      prompt,
      provider,
      ...options
    };

    const response = await this.makeRequest<{
      estimated_cost: number;
      provider: string;
      model?: string;
    }>('/cost/estimate', {
      method: 'POST',
      body: JSON.stringify(request)
    });
    return response.data;
  }

  async healthCheck(): Promise<Record<string, boolean>> {
    const response = await this.makeRequest<Record<string, boolean>>('/health');
    return response.data;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    };

    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: ApiResponse<T> = await response.json();
    
    if (!data.success) {
      throw new Error(data.message || 'API request failed');
    }

    return data;
  }
}