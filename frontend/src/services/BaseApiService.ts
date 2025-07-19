import { HttpClient } from '@utils/HttpClient';

/**
 * Abstract base service class for API communication
 * Provides common HTTP methods and error handling
 */
export abstract class BaseApiService {
  protected httpClient: HttpClient;
  protected baseUrl: string;
  protected endpoint: string;

  constructor(endpoint: string, baseUrl: string = '/api') {
    this.baseUrl = baseUrl;
    this.endpoint = endpoint;
    this.httpClient = new HttpClient(baseUrl);
  }

  // Abstract methods
  abstract getResourceUrl(id?: string | number): string;

  // Common CRUD operations
  async findAll<T>(params?: Record<string, any>): Promise<T[]> {
    try {
      const response = await this.httpClient.get<T[]>(this.getResourceUrl(), { params });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async findById<T>(id: string | number): Promise<T> {
    try {
      const response = await this.httpClient.get<T>(this.getResourceUrl(id));
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async create<T>(data: Partial<T>): Promise<T> {
    try {
      const response = await this.httpClient.post<T>(this.getResourceUrl(), data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async update<T>(id: string | number, data: Partial<T>): Promise<T> {
    try {
      const response = await this.httpClient.put<T>(this.getResourceUrl(id), data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async patch<T>(id: string | number, data: Partial<T>): Promise<T> {
    try {
      const response = await this.httpClient.patch<T>(this.getResourceUrl(id), data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async delete(id: string | number): Promise<void> {
    try {
      await this.httpClient.delete(this.getResourceUrl(id));
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Utility methods
  async search<T>(query: string, params?: Record<string, any>): Promise<T[]> {
    try {
      const searchParams = { q: query, ...params };
      const response = await this.httpClient.get<T[]>(`${this.getResourceUrl()}/search`, { params: searchParams });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async count(params?: Record<string, any>): Promise<number> {
    try {
      const response = await this.httpClient.get<{ count: number }>(`${this.getResourceUrl()}/count`, { params });
      return response.data.count;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async exists(id: string | number): Promise<boolean> {
    try {
      await this.httpClient.head(this.getResourceUrl(id));
      return true;
    } catch (error) {
      if (this.isNotFoundError(error)) {
        return false;
      }
      throw this.handleError(error);
    }
  }

  // Pagination support
  async paginate<T>(page: number = 1, limit: number = 20, params?: Record<string, any>): Promise<{
    data: T[];
    pagination: {
      page: number;
      limit: number;
      total: number;
      totalPages: number;
      hasNext: boolean;
      hasPrev: boolean;
    }
  }> {
    try {
      const paginationParams = { page, limit, ...params };
      const response = await this.httpClient.get(this.getResourceUrl(), { params: paginationParams });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Bulk operations
  async bulkCreate<T>(items: Partial<T>[]): Promise<T[]> {
    try {
      const response = await this.httpClient.post<T[]>(`${this.getResourceUrl()}/bulk`, { items });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async bulkUpdate<T>(updates: Array<{ id: string | number; data: Partial<T> }>): Promise<T[]> {
    try {
      const response = await this.httpClient.patch<T[]>(`${this.getResourceUrl()}/bulk`, { updates });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async bulkDelete(ids: Array<string | number>): Promise<void> {
    try {
      await this.httpClient.delete(`${this.getResourceUrl()}/bulk`, { data: { ids } });
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Error handling
  protected handleError(error: any): Error {
    console.error(`API Error in ${this.constructor.name}:`, error);

    if (error.response) {
      // HTTP error response
      const { status, data } = error.response;
      const message = data?.message || data?.error || `HTTP ${status} Error`;
      
      switch (status) {
        case 400:
          return new Error(`Bad Request: ${message}`);
        case 401:
          return new Error(`Unauthorized: ${message}`);
        case 403:
          return new Error(`Forbidden: ${message}`);
        case 404:
          return new Error(`Not Found: ${message}`);
        case 422:
          return new Error(`Validation Error: ${message}`);
        case 429:
          return new Error(`Rate Limited: ${message}`);
        case 500:
          return new Error(`Server Error: ${message}`);
        default:
          return new Error(`API Error (${status}): ${message}`);
      }
    } else if (error.request) {
      // Network error
      return new Error('Network Error: Unable to connect to the server');
    } else {
      // Other error
      return new Error(error.message || 'Unknown Error');
    }
  }

  protected isNotFoundError(error: any): boolean {
    return error.response?.status === 404;
  }

  // Authentication helpers
  protected setAuthToken(token: string): void {
    this.httpClient.setAuthToken(token);
  }

  protected clearAuthToken(): void {
    this.httpClient.clearAuthToken();
  }

  // Request interceptors
  protected addRequestInterceptor(fn: (config: any) => any): void {
    this.httpClient.addRequestInterceptor(fn);
  }

  protected addResponseInterceptor(fn: (response: any) => any, errorFn?: (error: any) => any): void {
    this.httpClient.addResponseInterceptor(fn, errorFn);
  }

  // Caching support
  protected async getCached<T>(key: string): Promise<T | null> {
    try {
      const cached = localStorage.getItem(`api_cache_${key}`);
      if (cached) {
        const { data, expiry } = JSON.parse(cached);
        if (Date.now() < expiry) {
          return data;
        } else {
          localStorage.removeItem(`api_cache_${key}`);
        }
      }
    } catch (error) {
      console.warn('Cache retrieval failed:', error);
    }
    return null;
  }

  protected setCached<T>(key: string, data: T, ttlMinutes: number = 5): void {
    try {
      const expiry = Date.now() + (ttlMinutes * 60 * 1000);
      localStorage.setItem(`api_cache_${key}`, JSON.stringify({ data, expiry }));
    } catch (error) {
      console.warn('Cache storage failed:', error);
    }
  }

  protected clearCache(key?: string): void {
    if (key) {
      localStorage.removeItem(`api_cache_${key}`);
    } else {
      // Clear all cache entries for this service
      const keys = Object.keys(localStorage).filter(k => k.startsWith('api_cache_'));
      keys.forEach(k => localStorage.removeItem(k));
    }
  }
}