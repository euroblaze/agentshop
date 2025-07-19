import { BaseModel } from './BaseModel';

export interface CustomerAddress {
  line1: string;
  line2?: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
}

export interface CustomerPreferences {
  emailMarketing: boolean;
  smsMarketing: boolean;
  newsletter: boolean;
  language: string;
  currency: string;
  timezone: string;
}

export interface CustomerStats {
  totalOrders: number;
  totalSpent: number;
  averageOrderValue: number;
  lastOrderDate?: Date;
  favoriteCategories: string[];
  loyaltyPoints: number;
}

export interface CustomerData {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  phone?: string;
  dateOfBirth?: Date;
  
  // Address
  address: CustomerAddress;
  
  // Account status
  isActive: boolean;
  emailVerified: boolean;
  lastLogin?: Date;
  
  // Preferences
  preferences: CustomerPreferences;
  
  // Statistics
  stats: CustomerStats;
  
  // Metadata
  registrationIp?: string;
  userAgent?: string;
  referralSource?: string;
  
  // Timestamps
  createdAt: Date;
  updatedAt: Date;
}

export class Customer extends BaseModel {
  private _email: string = '';
  private _firstName: string = '';
  private _lastName: string = '';
  private _phone?: string;
  private _dateOfBirth?: Date;
  private _address: CustomerAddress = {
    line1: '',
    city: '',
    state: '',
    postalCode: '',
    country: ''
  };
  private _isActive: boolean = true;
  private _emailVerified: boolean = false;
  private _lastLogin?: Date;
  private _preferences: CustomerPreferences = {
    emailMarketing: false,
    smsMarketing: false,
    newsletter: false,
    language: 'en',
    currency: 'USD',
    timezone: 'UTC'
  };
  private _stats: CustomerStats = {
    totalOrders: 0,
    totalSpent: 0,
    averageOrderValue: 0,
    favoriteCategories: [],
    loyaltyPoints: 0
  };
  private _registrationIp?: string;
  private _userAgent?: string;
  private _referralSource?: string;

  // Getters
  get email(): string { return this._email; }
  get firstName(): string { return this._firstName; }
  get lastName(): string { return this._lastName; }
  get phone(): string | undefined { return this._phone; }
  get dateOfBirth(): Date | undefined { return this._dateOfBirth; }
  get address(): CustomerAddress { return this._address; }
  get isActive(): boolean { return this._isActive; }
  get emailVerified(): boolean { return this._emailVerified; }
  get lastLogin(): Date | undefined { return this._lastLogin; }
  get preferences(): CustomerPreferences { return this._preferences; }
  get stats(): CustomerStats { return this._stats; }
  get registrationIp(): string | undefined { return this._registrationIp; }
  get userAgent(): string | undefined { return this._userAgent; }
  get referralSource(): string | undefined { return this._referralSource; }

  // Setters
  set email(value: string) { this._email = value; }
  set firstName(value: string) { this._firstName = value; }
  set lastName(value: string) { this._lastName = value; }
  set phone(value: string | undefined) { this._phone = value; }
  set dateOfBirth(value: Date | undefined) { this._dateOfBirth = value; }

  // Computed properties
  get fullName(): string {
    return `${this._firstName} ${this._lastName}`.trim();
  }

  get initials(): string {
    return `${this._firstName.charAt(0)}${this._lastName.charAt(0)}`.toUpperCase();
  }

  get displayName(): string {
    return this.fullName || this._email;
  }

  get age(): number | undefined {
    if (!this._dateOfBirth) return undefined;
    const today = new Date();
    const birthDate = new Date(this._dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    
    return age;
  }

  get formattedAddress(): string {
    const { line1, line2, city, state, postalCode, country } = this._address;
    const parts = [
      line1,
      line2,
      `${city}, ${state} ${postalCode}`,
      country
    ].filter(Boolean);
    
    return parts.join('\n');
  }

  get isNewCustomer(): boolean {
    return this._stats.totalOrders === 0;
  }

  get isVipCustomer(): boolean {
    return this._stats.totalSpent >= 1000 || this._stats.totalOrders >= 10;
  }

  get loyaltyTier(): 'bronze' | 'silver' | 'gold' | 'platinum' {
    if (this._stats.loyaltyPoints >= 10000) return 'platinum';
    if (this._stats.loyaltyPoints >= 5000) return 'gold';
    if (this._stats.loyaltyPoints >= 1000) return 'silver';
    return 'bronze';
  }

  get formattedTotalSpent(): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: this._preferences.currency
    }).format(this._stats.totalSpent);
  }

  get daysSinceLastLogin(): number | undefined {
    if (!this._lastLogin) return undefined;
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - this._lastLogin.getTime());
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }

  // Validation
  validate(): boolean {
    this.clearErrors();
    let isValid = true;

    // Email validation
    if (!this.validateRequired(this._email, 'email')) {
      isValid = false;
    } else if (!this.validateEmail(this._email, 'email')) {
      isValid = false;
    }

    // Name validation
    if (!this.validateRequired(this._firstName, 'firstName')) {
      isValid = false;
    }
    if (!this.validateRequired(this._lastName, 'lastName')) {
      isValid = false;
    }

    // Phone validation
    if (this._phone && !this.validatePhoneNumber(this._phone)) {
      isValid = false;
    }

    // Date of birth validation
    if (this._dateOfBirth && !this.validateDateOfBirth(this._dateOfBirth)) {
      isValid = false;
    }

    // Address validation
    if (!this.validateAddress()) {
      isValid = false;
    }

    return isValid;
  }

  private validatePhoneNumber(phone: string): boolean {
    const phoneRegex = /^\+?[\d\s\-\(\)]+$/;
    if (!phoneRegex.test(phone)) {
      this.addError('phone', 'Please enter a valid phone number');
      return false;
    }
    this.removeError('phone');
    return true;
  }

  private validateDateOfBirth(dateOfBirth: Date): boolean {
    const now = new Date();
    const age = now.getFullYear() - dateOfBirth.getFullYear();
    
    if (age < 13) {
      this.addError('dateOfBirth', 'Must be at least 13 years old');
      return false;
    }
    
    if (age > 120) {
      this.addError('dateOfBirth', 'Please enter a valid date of birth');
      return false;
    }
    
    this.removeError('dateOfBirth');
    return true;
  }

  private validateAddress(): boolean {
    let isValid = true;
    
    if (!this._address.line1.trim()) {
      this.addError('address.line1', 'Address line 1 is required');
      isValid = false;
    }
    
    if (!this._address.city.trim()) {
      this.addError('address.city', 'City is required');
      isValid = false;
    }
    
    if (!this._address.state.trim()) {
      this.addError('address.state', 'State is required');
      isValid = false;
    }
    
    if (!this._address.postalCode.trim()) {
      this.addError('address.postalCode', 'Postal code is required');
      isValid = false;
    }
    
    if (!this._address.country.trim()) {
      this.addError('address.country', 'Country is required');
      isValid = false;
    }
    
    return isValid;
  }

  // Serialization
  toJson(): Record<string, any> {
    return {
      id: this._id,
      email: this._email,
      firstName: this._firstName,
      lastName: this._lastName,
      phone: this._phone,
      dateOfBirth: this.formatDate(this._dateOfBirth),
      address: this._address,
      isActive: this._isActive,
      emailVerified: this._emailVerified,
      lastLogin: this.formatDate(this._lastLogin),
      preferences: this._preferences,
      stats: this._stats,
      registrationIp: this._registrationIp,
      userAgent: this._userAgent,
      referralSource: this._referralSource,
      createdAt: this.formatDate(this._createdAt),
      updatedAt: this.formatDate(this._updatedAt),
    };
  }

  fromJson(data: Record<string, any>): void {
    this._id = data.id;
    this._email = data.email || '';
    this._firstName = data.firstName || '';
    this._lastName = data.lastName || '';
    this._phone = data.phone;
    this._dateOfBirth = this.parseDate(data.dateOfBirth);
    this._address = { ...this._address, ...data.address };
    this._isActive = data.isActive !== undefined ? data.isActive : true;
    this._emailVerified = data.emailVerified || false;
    this._lastLogin = this.parseDate(data.lastLogin);
    this._preferences = { ...this._preferences, ...data.preferences };
    this._stats = { ...this._stats, ...data.stats };
    this._registrationIp = data.registrationIp;
    this._userAgent = data.userAgent;
    this._referralSource = data.referralSource;
    this._createdAt = this.parseDate(data.createdAt);
    this._updatedAt = this.parseDate(data.updatedAt);
  }

  // Business methods
  updateStats(orderValue: number): void {
    this._stats.totalOrders++;
    this._stats.totalSpent += orderValue;
    this._stats.averageOrderValue = this._stats.totalSpent / this._stats.totalOrders;
    this._stats.lastOrderDate = new Date();
    
    // Add loyalty points (1 point per dollar spent)
    this._stats.loyaltyPoints += Math.floor(orderValue);
  }

  updateLastLogin(): void {
    this._lastLogin = new Date();
  }

  verifyEmail(): void {
    this._emailVerified = true;
  }

  deactivate(): void {
    this._isActive = false;
  }

  activate(): void {
    this._isActive = true;
  }

  updateAddress(address: Partial<CustomerAddress>): void {
    this._address = { ...this._address, ...address };
  }

  updatePreferences(preferences: Partial<CustomerPreferences>): void {
    this._preferences = { ...this._preferences, ...preferences };
  }

  addFavoriteCategory(category: string): void {
    if (!this._stats.favoriteCategories.includes(category)) {
      this._stats.favoriteCategories.push(category);
    }
  }

  removeFavoriteCategory(category: string): void {
    this._stats.favoriteCategories = this._stats.favoriteCategories.filter(c => c !== category);
  }

  // Utility methods
  getPersonalizedGreeting(): string {
    const hour = new Date().getHours();
    let timeOfDay = 'Hello';
    
    if (hour < 12) timeOfDay = 'Good morning';
    else if (hour < 17) timeOfDay = 'Good afternoon';
    else timeOfDay = 'Good evening';
    
    return `${timeOfDay}, ${this._firstName}!`;
  }

  canReceiveMarketing(): boolean {
    return this._preferences.emailMarketing && this._emailVerified;
  }

  getTimezoneOffset(): number {
    // This is a simplified implementation
    // In a real app, you'd use a proper timezone library
    return new Date().getTimezoneOffset();
  }

  formatDateInTimezone(date: Date): string {
    // Simplified timezone formatting
    return new Intl.DateTimeFormat('en-US', {
      timeZone: this._preferences.timezone,
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  }

  // Search and filtering helpers
  matchesSearch(query: string): boolean {
    const searchText = query.toLowerCase();
    return (
      this._email.toLowerCase().includes(searchText) ||
      this._firstName.toLowerCase().includes(searchText) ||
      this._lastName.toLowerCase().includes(searchText) ||
      (this._phone && this._phone.includes(searchText))
    );
  }

  // Export data for GDPR compliance
  exportPersonalData(): Record<string, any> {
    return {
      personalInfo: {
        email: this._email,
        firstName: this._firstName,
        lastName: this._lastName,
        phone: this._phone,
        dateOfBirth: this._dateOfBirth,
      },
      address: this._address,
      preferences: this._preferences,
      stats: this._stats,
      metadata: {
        registrationIp: this._registrationIp,
        userAgent: this._userAgent,
        referralSource: this._referralSource,
        createdAt: this._createdAt,
        lastLogin: this._lastLogin,
      }
    };
  }
}