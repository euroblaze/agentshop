/**
 * Abstract base class for all frontend data models
 * Provides common functionality for data validation, serialization, and state management
 */
export abstract class BaseModel {
  protected _id?: string | number;
  protected _createdAt?: Date;
  protected _updatedAt?: Date;
  protected _isLoading: boolean = false;
  protected _errors: Record<string, string> = {};

  constructor(data?: Partial<any>) {
    if (data) {
      this.fromJson(data);
    }
  }

  // Abstract methods that must be implemented by child classes
  abstract validate(): boolean;
  abstract toJson(): Record<string, any>;
  abstract fromJson(data: Record<string, any>): void;

  // Common getters
  get id(): string | number | undefined {
    return this._id;
  }

  get createdAt(): Date | undefined {
    return this._createdAt;
  }

  get updatedAt(): Date | undefined {
    return this._updatedAt;
  }

  get isLoading(): boolean {
    return this._isLoading;
  }

  get errors(): Record<string, string> {
    return this._errors;
  }

  get hasErrors(): boolean {
    return Object.keys(this._errors).length > 0;
  }

  // Common methods
  setLoading(loading: boolean): void {
    this._isLoading = loading;
  }

  addError(field: string, message: string): void {
    this._errors[field] = message;
  }

  removeError(field: string): void {
    delete this._errors[field];
  }

  clearErrors(): void {
    this._errors = {};
  }

  getError(field: string): string | undefined {
    return this._errors[field];
  }

  // Utility methods
  clone(): this {
    const cloned = Object.create(Object.getPrototypeOf(this));
    return Object.assign(cloned, JSON.parse(JSON.stringify(this.toJson())));
  }

  equals(other: BaseModel): boolean {
    return JSON.stringify(this.toJson()) === JSON.stringify(other.toJson());
  }

  // Date handling utilities
  protected parseDate(dateString: string | Date | undefined): Date | undefined {
    if (!dateString) return undefined;
    if (dateString instanceof Date) return dateString;
    return new Date(dateString);
  }

  protected formatDate(date: Date | undefined): string | undefined {
    if (!date) return undefined;
    return date.toISOString();
  }

  // Validation helpers
  protected validateRequired(value: any, fieldName: string): boolean {
    if (value === null || value === undefined || value === '') {
      this.addError(fieldName, `${fieldName} is required`);
      return false;
    }
    this.removeError(fieldName);
    return true;
  }

  protected validateEmail(email: string, fieldName: string = 'email'): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      this.addError(fieldName, 'Please enter a valid email address');
      return false;
    }
    this.removeError(fieldName);
    return true;
  }

  protected validateMinLength(value: string, minLength: number, fieldName: string): boolean {
    if (value.length < minLength) {
      this.addError(fieldName, `${fieldName} must be at least ${minLength} characters long`);
      return false;
    }
    this.removeError(fieldName);
    return true;
  }

  protected validateMaxLength(value: string, maxLength: number, fieldName: string): boolean {
    if (value.length > maxLength) {
      this.addError(fieldName, `${fieldName} must be no more than ${maxLength} characters long`);
      return false;
    }
    this.removeError(fieldName);
    return true;
  }

  protected validateNumeric(value: any, fieldName: string): boolean {
    if (isNaN(Number(value))) {
      this.addError(fieldName, `${fieldName} must be a valid number`);
      return false;
    }
    this.removeError(fieldName);
    return true;
  }

  protected validatePositive(value: number, fieldName: string): boolean {
    if (value <= 0) {
      this.addError(fieldName, `${fieldName} must be greater than 0`);
      return false;
    }
    this.removeError(fieldName);
    return true;
  }

  // State management helpers
  setState(updates: Partial<this>): void {
    Object.assign(this, updates);
  }

  // Debugging helpers
  debug(): void {
    console.log(`${this.constructor.name}:`, this.toJson());
  }
}