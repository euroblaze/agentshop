/**
 * Frontend Security Service - Client-side security utilities
 */

export class SecurityService {
  private static instance: SecurityService;
  private sessionId: string;
  private csrfToken: string | null = null;

  private constructor() {
    this.sessionId = this.generateSessionId();
    this.initializeSecurity();
  }

  public static getInstance(): SecurityService {
    if (!SecurityService.instance) {
      SecurityService.instance = new SecurityService();
    }
    return SecurityService.instance;
  }

  private initializeSecurity(): void {
    // Set up security headers for all HTTP requests
    this.setupSecureDefaults();
    
    // Initialize CSRF protection
    this.initializeCSRF();
    
    // Set up XSS protection
    this.setupXSSProtection();
    
    // Monitor for security violations
    this.setupSecurityMonitoring();
  }

  private generateSessionId(): string {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  public getSessionId(): string {
    return this.sessionId;
  }

  private setupSecureDefaults(): void {
    // Add security headers to HTTP client
    const httpClient = this.getHttpClient();
    if (httpClient) {
      httpClient.setDefaultHeader('X-Session-ID', this.sessionId);
      httpClient.setDefaultHeader('X-Requested-With', 'XMLHttpRequest');
    }
  }

  private initializeCSRF(): void {
    // Get CSRF token from meta tag or cookie
    const metaToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    const cookieToken = this.getCookie('csrf_token');
    
    this.csrfToken = metaToken || cookieToken;
    
    if (this.csrfToken) {
      const httpClient = this.getHttpClient();
      if (httpClient) {
        httpClient.setDefaultHeader('X-CSRF-Token', this.csrfToken);
      }
    }
  }

  private setupXSSProtection(): void {
    // Set up Content Security Policy monitoring
    document.addEventListener('securitypolicyviolation', (event) => {
      console.error('CSP Violation:', event);
      this.reportSecurityViolation('csp', {
        blockedURI: event.blockedURI,
        violatedDirective: event.violatedDirective,
        originalPolicy: event.originalPolicy
      });
    });
  }

  private setupSecurityMonitoring(): void {
    // Monitor for potential security issues
    this.monitorConsoleAccess();
    this.monitorDevTools();
    this.monitorNetworkRequests();
  }

  private monitorConsoleAccess(): void {
    // Detect console access (potential XSS)
    const originalLog = console.log;
    console.log = (...args: any[]) => {
      // Check for suspicious console usage
      const argString = args.join(' ');
      if (this.containsSuspiciousContent(argString)) {
        this.reportSecurityViolation('console_access', { content: argString });
      }
      originalLog.apply(console, args);
    };
  }

  private monitorDevTools(): void {
    // Detect developer tools (simple detection)
    let devtools = { open: false };
    const threshold = 160;

    setInterval(() => {
      if (
        window.outerHeight - window.innerHeight > threshold ||
        window.outerWidth - window.innerWidth > threshold
      ) {
        if (!devtools.open) {
          devtools.open = true;
          this.reportSecurityViolation('devtools_detected', {});
        }
      } else {
        devtools.open = false;
      }
    }, 500);
  }

  private monitorNetworkRequests(): void {
    // Monitor for suspicious network requests
    const originalFetch = window.fetch;
    window.fetch = async (...args: any[]) => {
      const [url, options] = args;
      
      // Check for suspicious URLs
      if (this.isSuspiciousURL(url)) {
        this.reportSecurityViolation('suspicious_request', { url });
        throw new Error('Request blocked for security reasons');
      }
      
      return originalFetch.apply(window, args);
    };
  }

  private containsSuspiciousContent(content: string): boolean {
    const suspiciousPatterns = [
      /<script[^>]*>/i,
      /javascript:/i,
      /on\w+\s*=/i,
      /eval\s*\(/i,
      /function\s*\(\s*\)\s*{/i
    ];
    
    return suspiciousPatterns.some(pattern => pattern.test(content));
  }

  private isSuspiciousURL(url: string): boolean {
    try {
      const urlObj = new URL(url, window.location.origin);
      
      // Check for suspicious protocols
      if (!['http:', 'https:'].includes(urlObj.protocol)) {
        return true;
      }
      
      // Check for suspicious domains (if not same origin)
      if (urlObj.origin !== window.location.origin) {
        const suspiciousDomains = [
          'eval',
          'javascript',
          'data:',
          'vbscript:'
        ];
        
        return suspiciousDomains.some(domain => 
          urlObj.hostname.includes(domain) || urlObj.href.includes(domain)
        );
      }
      
      return false;
    } catch {
      return true; // Invalid URL
    }
  }

  private reportSecurityViolation(type: string, details: any): void {
    // Report security violations to backend
    const violation = {
      type,
      details,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      sessionId: this.sessionId
    };
    
    // Send to security endpoint (fire and forget)
    fetch('/api/security/violations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': this.sessionId
      },
      body: JSON.stringify(violation)
    }).catch(() => {
      // Silently fail - don't block user experience
    });
  }

  public sanitizeInput(input: string): string {
    if (!input) return '';
    
    // Remove potentially dangerous characters
    return input
      .replace(/[<>'"&]/g, (char) => {
        const entities: { [key: string]: string } = {
          '<': '&lt;',
          '>': '&gt;',
          '"': '&quot;',
          "'": '&#x27;',
          '&': '&amp;'
        };
        return entities[char] || char;
      })
      .trim()
      .slice(0, 1000); // Limit length
  }

  public validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email) && email.length <= 255;
  }

  public validatePassword(password: string): {
    valid: boolean;
    errors: string[];
    strength: 'weak' | 'medium' | 'strong';
  } {
    const errors: string[] = [];
    let score = 0;

    if (password.length < 8) {
      errors.push('Password must be at least 8 characters long');
    } else if (password.length >= 12) {
      score += 2;
    } else {
      score += 1;
    }

    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain lowercase letters');
    } else {
      score += 1;
    }

    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain uppercase letters');
    } else {
      score += 1;
    }

    if (!/\d/.test(password)) {
      errors.push('Password must contain numbers');
    } else {
      score += 1;
    }

    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      errors.push('Password must contain special characters');
    } else {
      score += 2;
    }

    // Check for common passwords
    const commonPasswords = [
      'password', '123456', '123456789', 'qwerty', 'abc123',
      'password123', 'admin', 'letmein', 'welcome'
    ];
    
    if (commonPasswords.includes(password.toLowerCase())) {
      errors.push('Password is too common');
      score = 0;
    }

    let strength: 'weak' | 'medium' | 'strong';
    if (score >= 6) {
      strength = 'strong';
    } else if (score >= 4) {
      strength = 'medium';
    } else {
      strength = 'weak';
    }

    return {
      valid: errors.length === 0,
      errors,
      strength
    };
  }

  public secureStorage = {
    set: (key: string, value: string, expirationHours: number = 24): void => {
      const item = {
        value,
        expiry: Date.now() + (expirationHours * 60 * 60 * 1000)
      };
      
      try {
        sessionStorage.setItem(key, JSON.stringify(item));
      } catch (error) {
        console.error('Secure storage set failed:', error);
      }
    },

    get: (key: string): string | null => {
      try {
        const itemStr = sessionStorage.getItem(key);
        if (!itemStr) return null;

        const item = JSON.parse(itemStr);
        if (Date.now() > item.expiry) {
          sessionStorage.removeItem(key);
          return null;
        }

        return item.value;
      } catch (error) {
        console.error('Secure storage get failed:', error);
        return null;
      }
    },

    remove: (key: string): void => {
      try {
        sessionStorage.removeItem(key);
      } catch (error) {
        console.error('Secure storage remove failed:', error);
      }
    },

    clear: (): void => {
      try {
        sessionStorage.clear();
      } catch (error) {
        console.error('Secure storage clear failed:', error);
      }
    }
  };

  public maskSensitiveData = {
    email: (email: string): string => {
      if (!email || !email.includes('@')) return email;
      const [local, domain] = email.split('@');
      if (local.length <= 2) return '*'.repeat(local.length) + '@' + domain;
      return local[0] + '*'.repeat(local.length - 2) + local.slice(-1) + '@' + domain;
    },

    phone: (phone: string): string => {
      if (!phone || phone.length < 4) return phone;
      return '*'.repeat(phone.length - 4) + phone.slice(-4);
    },

    creditCard: (cardNumber: string): string => {
      if (!cardNumber || cardNumber.length < 4) return cardNumber;
      return '*'.repeat(cardNumber.length - 4) + cardNumber.slice(-4);
    }
  };

  private getCookie(name: string): string | null {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop()?.split(';').shift() || null;
    }
    return null;
  }

  private getHttpClient(): any {
    // Get reference to HTTP client if available
    try {
      // This would depend on your HTTP client implementation
      return (window as any).httpClient;
    } catch {
      return null;
    }
  }

  public encryptLocalData(data: string, key: string): string {
    // Simple XOR encryption for local data (not cryptographically secure)
    let result = '';
    for (let i = 0; i < data.length; i++) {
      result += String.fromCharCode(
        data.charCodeAt(i) ^ key.charCodeAt(i % key.length)
      );
    }
    return btoa(result);
  }

  public decryptLocalData(encryptedData: string, key: string): string {
    try {
      const data = atob(encryptedData);
      let result = '';
      for (let i = 0; i < data.length; i++) {
        result += String.fromCharCode(
          data.charCodeAt(i) ^ key.charCodeAt(i % key.length)
        );
      }
      return result;
    } catch {
      return '';
    }
  }

  public generateCSRFToken(): string {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  public isSecureContext(): boolean {
    return window.isSecureContext && location.protocol === 'https:';
  }

  public validateOrigin(allowedOrigins: string[]): boolean {
    return allowedOrigins.includes(window.location.origin);
  }
}

// Export singleton instance
export const securityService = SecurityService.getInstance();

// Security configuration
export const SECURITY_CONFIG = {
  PASSWORD_MIN_LENGTH: 8,
  PASSWORD_MAX_LENGTH: 128,
  SESSION_TIMEOUT: 30 * 60 * 1000, // 30 minutes
  MAX_LOGIN_ATTEMPTS: 5,
  SECURE_HEADERS: {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin'
  }
};