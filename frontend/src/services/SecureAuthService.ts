import { BaseApiService } from './BaseApiService';
import { Customer } from '../models/Customer';
import { securityService } from '../security/SecurityService';

export class SecureAuthService {
  private httpClient = BaseApiService.getHttpClient();
  private basePath = '/auth';
  private refreshToken: string | null = null;
  private tokenRefreshPromise: Promise<string | null> | null = null;
  private refreshTimer: NodeJS.Timeout | null = null;

  async login(email: string, password: string): Promise<{ token: string, customer: Customer } | null> {
    try {
      // Validate inputs with security service
      if (!securityService.validateEmail(email)) {
        throw new Error('Invalid email format');
      }
      
      const passwordValidation = securityService.validatePassword(password);
      if (!passwordValidation.valid) {
        throw new Error('Password does not meet security requirements');
      }

      const response = await this.httpClient.post(`${this.basePath}/login`, {
        email: securityService.sanitizeInput(email),
        password, // Don't sanitize password
        session_id: securityService.getSessionId(),
        fingerprint: await this.generateDeviceFingerprint()
      });
      
      if (response.data.access_token) {
        // Store tokens securely
        securityService.secureStorage.set('auth_token', response.data.access_token, 1); // 1 hour
        
        if (response.data.refresh_token) {
          this.refreshToken = response.data.refresh_token;
          securityService.secureStorage.set('refresh_token', response.data.refresh_token, 168); // 7 days
        }
        
        // Set token in HTTP client
        this.httpClient.setAuthToken(response.data.access_token);
        
        // Set up automatic token refresh
        this.setupTokenRefresh(response.data.expires_in || 900); // Default 15 minutes
        
        // Clear any previous failed login attempts
        this.clearFailedAttempts();
        
        return {
          token: response.data.access_token,
          customer: new Customer(response.data.customer)
        };
      }
      return null;
    } catch (error: any) {
      // Track failed login attempts
      this.trackFailedAttempt();
      
      console.error('Login error:', error);
      throw error;
    }
  }

  async register(customerData: {
    email: string;
    password: string;
    firstName: string;
    lastName: string;
    phone?: string;
  }): Promise<{ token: string, customer: Customer } | null> {
    try {
      // Validate all inputs
      if (!securityService.validateEmail(customerData.email)) {
        throw new Error('Invalid email format');
      }
      
      const passwordValidation = securityService.validatePassword(customerData.password);
      if (!passwordValidation.valid) {
        throw new Error(`Password requirements: ${passwordValidation.errors.join(', ')}`);
      }

      // Sanitize text inputs
      const sanitizedData = {
        email: securityService.sanitizeInput(customerData.email),
        password: customerData.password, // Don't sanitize password
        first_name: securityService.sanitizeInput(customerData.firstName),
        last_name: securityService.sanitizeInput(customerData.lastName),
        phone: customerData.phone ? securityService.sanitizeInput(customerData.phone) : undefined,
        session_id: securityService.getSessionId(),
        fingerprint: await this.generateDeviceFingerprint()
      };

      const response = await this.httpClient.post(`${this.basePath}/register`, sanitizedData);
      
      if (response.data.access_token) {
        // Store tokens securely
        securityService.secureStorage.set('auth_token', response.data.access_token, 1);
        
        if (response.data.refresh_token) {
          this.refreshToken = response.data.refresh_token;
          securityService.secureStorage.set('refresh_token', response.data.refresh_token, 168);
        }
        
        this.httpClient.setAuthToken(response.data.access_token);
        this.setupTokenRefresh(response.data.expires_in || 900);
        
        return {
          token: response.data.access_token,
          customer: new Customer(response.data.customer)
        };
      }
      return null;
    } catch (error: any) {
      console.error('Registration error:', error);
      throw error;
    }
  }

  async refreshAccessToken(): Promise<string | null> {
    // Prevent multiple simultaneous refresh attempts
    if (this.tokenRefreshPromise) {
      return this.tokenRefreshPromise;
    }

    this.tokenRefreshPromise = this.performTokenRefresh();
    const result = await this.tokenRefreshPromise;
    this.tokenRefreshPromise = null;
    
    return result;
  }

  private async performTokenRefresh(): Promise<string | null> {
    try {
      const refreshToken = securityService.secureStorage.get('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await this.httpClient.post(`${this.basePath}/refresh`, {
        refresh_token: refreshToken,
        session_id: securityService.getSessionId()
      });

      if (response.data.access_token) {
        const newToken = response.data.access_token;
        
        // Store new token
        securityService.secureStorage.set('auth_token', newToken, 1);
        this.httpClient.setAuthToken(newToken);
        
        // Update refresh token if provided
        if (response.data.refresh_token) {
          this.refreshToken = response.data.refresh_token;
          securityService.secureStorage.set('refresh_token', response.data.refresh_token, 168);
        }
        
        // Schedule next refresh
        this.setupTokenRefresh(response.data.expires_in || 900);
        
        return newToken;
      }
      
      throw new Error('Token refresh failed');
    } catch (error) {
      console.error('Token refresh error:', error);
      
      // If refresh fails, logout user
      await this.logout();
      
      // Redirect to login page
      window.location.href = '/login';
      
      return null;
    }
  }

  private setupTokenRefresh(expiresIn: number): void {
    // Clear existing timer
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }
    
    // Refresh token 5 minutes before expiry
    const refreshTime = Math.max(300000, (expiresIn - 300) * 1000); // 5 minutes buffer
    
    this.refreshTimer = setTimeout(() => {
      this.refreshAccessToken();
    }, refreshTime);
  }

  async logout(): Promise<void> {
    try {
      // Clear refresh timer
      if (this.refreshTimer) {
        clearTimeout(this.refreshTimer);
        this.refreshTimer = null;
      }

      // Notify backend of logout
      const refreshToken = securityService.secureStorage.get('refresh_token');
      if (refreshToken) {
        await this.httpClient.post(`${this.basePath}/logout`, {
          refresh_token: refreshToken,
          session_id: securityService.getSessionId()
        });
      }
    } catch (error) {
      // Continue with logout even if API call fails
      console.error('Logout API error:', error);
    } finally {
      // Clear all stored tokens and session data
      securityService.secureStorage.clear();
      this.httpClient.clearAuthToken();
      this.refreshToken = null;
      
      // Clear failed login attempts
      this.clearFailedAttempts();
    }
  }

  async forgotPassword(email: string): Promise<boolean> {
    try {
      if (!securityService.validateEmail(email)) {
        throw new Error('Invalid email format');
      }

      await this.httpClient.post(`${this.basePath}/forgot-password`, {
        email: securityService.sanitizeInput(email),
        session_id: securityService.getSessionId()
      });
      
      return true;
    } catch (error) {
      console.error('Forgot password error:', error);
      return false;
    }
  }

  async resetPassword(token: string, newPassword: string): Promise<boolean> {
    try {
      const passwordValidation = securityService.validatePassword(newPassword);
      if (!passwordValidation.valid) {
        throw new Error(`Password requirements: ${passwordValidation.errors.join(', ')}`);
      }

      await this.httpClient.post(`${this.basePath}/reset-password`, {
        token: securityService.sanitizeInput(token),
        new_password: newPassword,
        session_id: securityService.getSessionId()
      });
      
      return true;
    } catch (error) {
      console.error('Reset password error:', error);
      return false;
    }
  }

  async verifyEmail(token: string): Promise<boolean> {
    try {
      await this.httpClient.post(`${this.basePath}/verify-email`, {
        token: securityService.sanitizeInput(token),
        session_id: securityService.getSessionId()
      });
      return true;
    } catch (error) {
      console.error('Email verification error:', error);
      return false;
    }
  }

  isAuthenticated(): boolean {
    const token = securityService.secureStorage.get('auth_token');
    return !!token && !this.isTokenExpired(token);
  }

  getToken(): string | null {
    return securityService.secureStorage.get('auth_token');
  }

  private isTokenExpired(token: string): boolean {
    try {
      // Simple JWT expiry check (decode without verification)
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      return payload.exp && payload.exp < currentTime;
    } catch {
      return true; // Assume expired if can't decode
    }
  }

  // Initialize auth from stored token
  initializeAuth(): void {
    const token = this.getToken();
    if (token && !this.isTokenExpired(token)) {
      this.httpClient.setAuthToken(token);
      
      // Set up token refresh
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expiresIn = payload.exp - Math.floor(Date.now() / 1000);
      if (expiresIn > 0) {
        this.setupTokenRefresh(expiresIn);
      }
    } else if (token) {
      // Token exists but is expired, try to refresh
      this.refreshAccessToken();
    }
  }

  private async generateDeviceFingerprint(): Promise<string> {
    // Generate a device fingerprint for security
    const fingerprint = {
      userAgent: navigator.userAgent,
      language: navigator.language,
      platform: navigator.platform,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      screen: `${screen.width}x${screen.height}`,
      colorDepth: screen.colorDepth,
      cookieEnabled: navigator.cookieEnabled,
      doNotTrack: navigator.doNotTrack
    };

    // Create hash of fingerprint
    const encoder = new TextEncoder();
    const data = encoder.encode(JSON.stringify(fingerprint));
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  private trackFailedAttempt(): void {
    const attempts = parseInt(localStorage.getItem('login_attempts') || '0');
    const newAttempts = attempts + 1;
    
    localStorage.setItem('login_attempts', newAttempts.toString());
    localStorage.setItem('last_attempt', Date.now().toString());
    
    // Block further attempts after 5 failures
    if (newAttempts >= 5) {
      const blockUntil = Date.now() + (15 * 60 * 1000); // 15 minutes
      localStorage.setItem('blocked_until', blockUntil.toString());
    }
  }

  private clearFailedAttempts(): void {
    localStorage.removeItem('login_attempts');
    localStorage.removeItem('last_attempt');
    localStorage.removeItem('blocked_until');
  }

  isBlocked(): boolean {
    const blockedUntil = localStorage.getItem('blocked_until');
    if (blockedUntil) {
      const blockTime = parseInt(blockedUntil);
      if (Date.now() < blockTime) {
        return true;
      } else {
        // Block period expired, clear it
        this.clearFailedAttempts();
      }
    }
    return false;
  }

  getBlockTimeRemaining(): number {
    const blockedUntil = localStorage.getItem('blocked_until');
    if (blockedUntil) {
      const blockTime = parseInt(blockedUntil);
      const remaining = blockTime - Date.now();
      return Math.max(0, remaining);
    }
    return 0;
  }
}

// Export singleton instance
export const secureAuthService = new SecureAuthService();

// Initialize auth on module load
secureAuthService.initializeAuth();