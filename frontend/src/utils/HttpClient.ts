/**
 * HTTP request wrapper with interceptors and common functionality
 */

export interface HttpResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
  headers: Record<string, string>;
}

export interface HttpRequestConfig {
  headers?: Record<string, string>;
  params?: Record<string, any>;
  timeout?: number;
  withCredentials?: boolean;
}

export interface RequestInterceptor {
  (config: HttpRequestConfig): HttpRequestConfig | Promise<HttpRequestConfig>;
}

export interface ResponseInterceptor {
  onFulfilled?: (response: HttpResponse) => HttpResponse | Promise<HttpResponse>;
  onRejected?: (error: any) => any;
}

export class HttpClient {
  private baseURL: string;
  private defaultHeaders: Record<string, string>;
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];
  private timeout: number = 30000; // 30 seconds

  constructor(baseURL: string = '') {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
  }

  // Configuration methods
  setBaseURL(url: string): void {
    this.baseURL = url;
  }

  setTimeout(timeout: number): void {
    this.timeout = timeout;
  }

  setDefaultHeader(key: string, value: string): void {
    this.defaultHeaders[key] = value;
  }

  removeDefaultHeader(key: string): void {
    delete this.defaultHeaders[key];
  }

  // Authentication helpers
  setAuthToken(token: string): void {
    this.setDefaultHeader('Authorization', `Bearer ${token}`);
  }

  clearAuthToken(): void {
    this.removeDefaultHeader('Authorization');
  }

  // Interceptor management
  addRequestInterceptor(interceptor: RequestInterceptor): void {
    this.requestInterceptors.push(interceptor);
  }

  addResponseInterceptor(onFulfilled?: ResponseInterceptor['onFulfilled'], onRejected?: ResponseInterceptor['onRejected']): void {
    this.responseInterceptors.push({ onFulfilled, onRejected });
  }

  // HTTP methods
  async get<T = any>(url: string, config?: HttpRequestConfig): Promise<HttpResponse<T>> {
    return this.request<T>('GET', url, undefined, config);
  }

  async post<T = any>(url: string, data?: any, config?: HttpRequestConfig): Promise<HttpResponse<T>> {
    return this.request<T>('POST', url, data, config);
  }

  async put<T = any>(url: string, data?: any, config?: HttpRequestConfig): Promise<HttpResponse<T>> {
    return this.request<T>('PUT', url, data, config);
  }

  async patch<T = any>(url: string, data?: any, config?: HttpRequestConfig): Promise<HttpResponse<T>> {
    return this.request<T>('PATCH', url, data, config);
  }

  async delete<T = any>(url: string, config?: HttpRequestConfig): Promise<HttpResponse<T>> {
    return this.request<T>('DELETE', url, undefined, config);
  }

  async head<T = any>(url: string, config?: HttpRequestConfig): Promise<HttpResponse<T>> {
    return this.request<T>('HEAD', url, undefined, config);
  }

  async options<T = any>(url: string, config?: HttpRequestConfig): Promise<HttpResponse<T>> {
    return this.request<T>('OPTIONS', url, undefined, config);
  }

  // Core request method
  private async request<T>(
    method: string,
    url: string,
    data?: any,
    config: HttpRequestConfig = {}
  ): Promise<HttpResponse<T>> {
    try {
      // Build full URL
      const fullUrl = this.buildUrl(url);

      // Prepare request config
      let requestConfig: HttpRequestConfig = {
        ...config,
        headers: {
          ...this.defaultHeaders,
          ...config.headers,
        },
        timeout: config.timeout || this.timeout,
      };

      // Apply request interceptors
      for (const interceptor of this.requestInterceptors) {
        requestConfig = await interceptor(requestConfig);
      }

      // Build request options
      const requestOptions: RequestInit = {
        method,
        headers: requestConfig.headers,
        credentials: requestConfig.withCredentials ? 'include' : 'same-origin',
        signal: this.createAbortSignal(requestConfig.timeout || this.timeout),
      };

      // Add body for non-GET requests
      if (data && method !== 'GET' && method !== 'HEAD') {
        if (data instanceof FormData) {
          // Remove Content-Type header for FormData (browser will set it with boundary)
          delete requestOptions.headers!['Content-Type'];
          requestOptions.body = data;
        } else if (typeof data === 'object') {
          requestOptions.body = JSON.stringify(data);
        } else {
          requestOptions.body = data;
        }
      }

      // Add query parameters for GET requests
      const urlWithParams = this.addQueryParams(fullUrl, config.params);

      // Make the request
      const response = await fetch(urlWithParams, requestOptions);

      // Parse response
      const httpResponse = await this.parseResponse<T>(response);

      // Apply response interceptors
      let finalResponse = httpResponse;
      for (const interceptor of this.responseInterceptors) {
        if (interceptor.onFulfilled) {
          finalResponse = await interceptor.onFulfilled(finalResponse);
        }
      }

      return finalResponse;
    } catch (error) {
      // Apply error interceptors
      for (const interceptor of this.responseInterceptors) {
        if (interceptor.onRejected) {
          error = await interceptor.onRejected(error);
        }
      }
      throw error;
    }
  }

  // URL building helpers
  private buildUrl(url: string): string {
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }
    
    const base = this.baseURL.endsWith('/') ? this.baseURL.slice(0, -1) : this.baseURL;
    const path = url.startsWith('/') ? url : `/${url}`;
    
    return `${base}${path}`;
  }

  private addQueryParams(url: string, params?: Record<string, any>): string {
    if (!params || Object.keys(params).length === 0) {
      return url;
    }

    const urlObj = new URL(url, window.location.origin);
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        if (Array.isArray(value)) {
          value.forEach(v => urlObj.searchParams.append(key, String(v)));
        } else {
          urlObj.searchParams.set(key, String(value));
        }
      }
    });

    return urlObj.toString();
  }

  // Response parsing
  private async parseResponse<T>(response: Response): Promise<HttpResponse<T>> {
    const headers: Record<string, string> = {};
    response.headers.forEach((value, key) => {
      headers[key] = value;
    });

    let data: T;
    const contentType = response.headers.get('content-type') || '';

    try {
      if (contentType.includes('application/json')) {
        data = await response.json();
      } else if (contentType.includes('text/')) {
        data = await response.text() as unknown as T;
      } else {
        data = await response.blob() as unknown as T;
      }
    } catch (error) {
      // If parsing fails, try to get text
      try {
        data = await response.text() as unknown as T;
      } catch {
        data = null as unknown as T;
      }
    }

    const httpResponse: HttpResponse<T> = {
      data,
      status: response.status,
      statusText: response.statusText,
      headers,
    };

    // Check if response is successful
    if (!response.ok) {
      throw this.createError(httpResponse, `HTTP ${response.status}: ${response.statusText}`);
    }

    return httpResponse;
  }

  // Error handling
  private createError(response: HttpResponse, message: string): Error {
    const error = new Error(message);
    (error as any).response = response;
    (error as any).status = response.status;
    return error;
  }

  // Timeout handling
  private createAbortSignal(timeout: number): AbortSignal {
    const controller = new AbortController();
    setTimeout(() => controller.abort(), timeout);
    return controller.signal;
  }

  // Utility methods
  async upload<T = any>(
    url: string,
    file: File,
    config?: HttpRequestConfig & {
      onUploadProgress?: (progress: number) => void;
    }
  ): Promise<HttpResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    // Note: Progress tracking would require XMLHttpRequest instead of fetch
    // This is a simplified version
    return this.post<T>(url, formData, config);
  }

  async downloadFile(url: string, filename?: string): Promise<void> {
    try {
      const response = await this.get<Blob>(url);
      const blob = response.data;
      
      // Create download link
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename || 'download';
      
      // Trigger download
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Cleanup
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Download failed:', error);
      throw error;
    }
  }

  // Retry mechanism
  async retryRequest<T>(
    requestFn: () => Promise<HttpResponse<T>>,
    maxRetries: number = 3,
    retryDelay: number = 1000
  ): Promise<HttpResponse<T>> {
    let lastError: Error;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await requestFn();
      } catch (error) {
        lastError = error as Error;
        
        // Don't retry for client errors (4xx)
        if ((error as any).status >= 400 && (error as any).status < 500) {
          throw error;
        }

        if (attempt < maxRetries) {
          await this.delay(retryDelay * attempt); // Exponential backoff
        }
      }
    }

    throw lastError!;
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Request cancellation
  createCancelToken(): { token: AbortSignal; cancel: () => void } {
    const controller = new AbortController();
    return {
      token: controller.signal,
      cancel: () => controller.abort(),
    };
  }

  // Debug helpers
  debug(): void {
    console.log('HttpClient Configuration:', {
      baseURL: this.baseURL,
      defaultHeaders: this.defaultHeaders,
      timeout: this.timeout,
      requestInterceptors: this.requestInterceptors.length,
      responseInterceptors: this.responseInterceptors.length,
    });
  }
}