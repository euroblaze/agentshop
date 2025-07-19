export interface LLMRequest {
  prompt: string;
  provider?: string;
  model?: string;
  user_id?: number;
  session_id?: string;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  stream?: boolean;
  context?: Record<string, any>;
}

export interface LLMResponse {
  success: boolean;
  request_id: number;
  response_id: number;
  content: string;
  provider: string;
  model: string;
  tokens_used: number;
  cost: number;
  cached: boolean;
  processing_time_ms: number;
  metadata?: Record<string, any>;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
  request_id?: number;
  tokens_used?: number;
  cost?: number;
  provider?: string;
  model?: string;
}

export interface Conversation {
  id: number;
  session_id: string;
  user_id?: number;
  title?: string;
  message_count: number;
  total_cost: number;
  last_activity: string;
  is_active: boolean;
  default_provider?: string;
  default_model?: string;
}

export interface ChatResponse extends LLMResponse {
  conversation_id: number;
  user_message_id: number;
  assistant_message_id: number;
  message_count: number;
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

  async sendChatMessage(
    message: string,
    sessionId: string,
    options?: Partial<LLMRequest>
  ): Promise<ChatResponse> {
    const request = {
      message,
      session_id: sessionId,
      ...options
    };

    const response = await this.makeRequest<ChatResponse>('/chat/message', {
      method: 'POST',
      body: JSON.stringify(request)
    });
    return response.data;
  }

  async getChatHistory(sessionId: string, limit?: number): Promise<{
    conversation: Conversation | null;
    messages: ChatMessage[];
  }> {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    
    const response = await this.makeRequest<{
      conversation: Conversation | null;
      messages: ChatMessage[];
    }>(`/chat/history/${sessionId}?${params}`);
    return response.data;
  }

  async getUserConversations(userId: number, activeOnly: boolean = true): Promise<Conversation[]> {
    const params = new URLSearchParams();
    params.append('active_only', activeOnly.toString());
    
    const response = await this.makeRequest<Conversation[]>(
      `/chat/conversations/user/${userId}?${params}`
    );
    return response.data;
  }

  async compareProviders(
    prompt: string,
    providers: string[],
    options?: Partial<LLMRequest>
  ): Promise<{
    session_id: string;
    results: Record<string, { success: boolean; content?: string; error?: string; cost?: number }>;
    total_cost: number;
    providers_count: number;
    successful_count: number;
  }> {
    const request = {
      prompt,
      providers,
      ...options
    };

    const response = await this.makeRequest<{
      session_id: string;
      results: Record<string, any>;
      total_cost: number;
      providers_count: number;
      successful_count: number;
    }>('/chat/compare', {
      method: 'POST',
      body: JSON.stringify(request)
    });
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
    }>('/analytics/cost/estimate', {
      method: 'POST',
      body: JSON.stringify(request)
    });
    return response.data;
  }

  async healthCheck(): Promise<Record<string, boolean>> {
    const response = await this.makeRequest<Record<string, boolean>>('/analytics/health');
    return response.data;
  }

  async getUsageStatistics(
    periodType: 'hour' | 'day' | 'month' = 'day',
    days: number = 7,
    provider?: string
  ): Promise<any[]> {
    const params = new URLSearchParams();
    params.append('period_type', periodType);
    params.append('days', days.toString());
    if (provider) params.append('provider', provider);

    const response = await this.makeRequest<any[]>(`/analytics/usage?${params}`);
    return response.data;
  }

  async getProviderStatus(): Promise<any[]> {
    const response = await this.makeRequest<any[]>('/analytics/providers/status');
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