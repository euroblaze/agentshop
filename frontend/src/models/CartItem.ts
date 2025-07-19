import { BaseModel } from './BaseModel';

export interface CartItemData {
  id: string;
  productId: number;
  productName: string;
  productSlug: string;
  productImage?: string;
  productSku?: string;
  unitPrice: number;
  salePrice?: number;
  quantity: number;
  maxQuantity?: number;
  
  // Product details
  licenseType?: 'personal' | 'commercial' | 'enterprise';
  isDigital: boolean;
  downloadSize?: number;
  
  // Availability
  isAvailable: boolean;
  stockStatus?: 'in_stock' | 'out_of_stock' | 'limited';
  
  // Timestamps
  addedAt: Date;
  updatedAt?: Date;
}

export class CartItem extends BaseModel {
  private _productId: number = 0;
  private _productName: string = '';
  private _productSlug: string = '';
  private _productImage?: string;
  private _productSku?: string;
  private _unitPrice: number = 0;
  private _salePrice?: number;
  private _quantity: number = 1;
  private _maxQuantity?: number;
  private _licenseType?: CartItemData['licenseType'];
  private _isDigital: boolean = true;
  private _downloadSize?: number;
  private _isAvailable: boolean = true;
  private _stockStatus?: CartItemData['stockStatus'];
  private _addedAt: Date = new Date();
  private _updatedAt?: Date;

  constructor(data?: Partial<CartItemData>) {
    super();
    if (data) {
      this.fromJson(data);
    } else {
      this._id = this.generateId();
    }
  }

  // Getters
  get productId(): number { return this._productId; }
  get productName(): string { return this._productName; }
  get productSlug(): string { return this._productSlug; }
  get productImage(): string | undefined { return this._productImage; }
  get productSku(): string | undefined { return this._productSku; }
  get unitPrice(): number { return this._unitPrice; }
  get salePrice(): number | undefined { return this._salePrice; }
  get quantity(): number { return this._quantity; }
  get maxQuantity(): number | undefined { return this._maxQuantity; }
  get licenseType(): CartItemData['licenseType'] { return this._licenseType; }
  get isDigital(): boolean { return this._isDigital; }
  get downloadSize(): number | undefined { return this._downloadSize; }
  get isAvailable(): boolean { return this._isAvailable; }
  get stockStatus(): CartItemData['stockStatus'] { return this._stockStatus; }
  get addedAt(): Date { return this._addedAt; }
  get updatedAt(): Date | undefined { return this._updatedAt; }

  // Setters
  set quantity(value: number) {
    if (value > 0 && (!this._maxQuantity || value <= this._maxQuantity)) {
      this._quantity = value;
      this._updatedAt = new Date();
    }
  }

  set isAvailable(value: boolean) {
    this._isAvailable = value;
    this._updatedAt = new Date();
  }

  // Computed properties
  get effectivePrice(): number {
    return this._salePrice || this._unitPrice;
  }

  get totalPrice(): number {
    return this.effectivePrice * this._quantity;
  }

  get isOnSale(): boolean {
    return this._salePrice !== undefined && this._salePrice < this._unitPrice;
  }

  get discountAmount(): number {
    if (!this.isOnSale) return 0;
    return (this._unitPrice - this.effectivePrice) * this._quantity;
  }

  get discountPercentage(): number {
    if (!this.isOnSale) return 0;
    return Math.round(((this._unitPrice - this.effectivePrice) / this._unitPrice) * 100);
  }

  get formattedUnitPrice(): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(this._unitPrice);
  }

  get formattedEffectivePrice(): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(this.effectivePrice);
  }

  get formattedTotalPrice(): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(this.totalPrice);
  }

  get formattedDiscountAmount(): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(this.discountAmount);
  }

  get productUrl(): string {
    return `/products/${this._productSlug}`;
  }

  get canIncrease(): boolean {
    if (!this._isAvailable) return false;
    if (this._maxQuantity && this._quantity >= this._maxQuantity) return false;
    return true;
  }

  get canDecrease(): boolean {
    return this._quantity > 1;
  }

  get formattedDownloadSize(): string {
    if (!this._downloadSize) return '';
    
    const sizes = ['B', 'KB', 'MB', 'GB'];
    let size = this._downloadSize;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < sizes.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${sizes[unitIndex]}`;
  }

  get stockStatusDisplay(): string {
    switch (this._stockStatus) {
      case 'in_stock': return 'In Stock';
      case 'out_of_stock': return 'Out of Stock';
      case 'limited': return 'Limited Stock';
      default: return '';
    }
  }

  get availabilityText(): string {
    if (!this._isAvailable) return 'Currently Unavailable';
    if (this._stockStatus === 'out_of_stock') return 'Out of Stock';
    if (this._stockStatus === 'limited') return 'Limited Availability';
    return 'Available';
  }

  get warningMessages(): string[] {
    const warnings: string[] = [];
    
    if (!this._isAvailable) {
      warnings.push('This item is currently unavailable');
    }
    
    if (this._stockStatus === 'out_of_stock') {
      warnings.push('This item is out of stock');
    }
    
    if (this._stockStatus === 'limited') {
      warnings.push('Limited stock available');
    }
    
    if (this._maxQuantity && this._quantity >= this._maxQuantity) {
      warnings.push(`Maximum quantity: ${this._maxQuantity}`);
    }
    
    return warnings;
  }

  get hasWarnings(): boolean {
    return this.warningMessages.length > 0;
  }

  // Validation
  validate(): boolean {
    this.clearErrors();
    let isValid = true;

    if (!this.validateRequired(this._productId, 'productId') || this._productId <= 0) {
      this.addError('productId', 'Valid product ID is required');
      isValid = false;
    }

    if (!this.validateRequired(this._productName, 'productName')) {
      isValid = false;
    }

    if (!this.validateRequired(this._productSlug, 'productSlug')) {
      isValid = false;
    }

    if (!this.validatePositive(this._unitPrice, 'unitPrice')) {
      isValid = false;
    }

    if (!this.validatePositive(this._quantity, 'quantity')) {
      isValid = false;
    }

    if (this._maxQuantity && this._quantity > this._maxQuantity) {
      this.addError('quantity', `Quantity cannot exceed ${this._maxQuantity}`);
      isValid = false;
    }

    if (this._salePrice !== undefined && this._salePrice < 0) {
      this.addError('salePrice', 'Sale price cannot be negative');
      isValid = false;
    }

    return isValid;
  }

  // Serialization
  toJson(): Record<string, any> {
    return {
      id: this._id,
      productId: this._productId,
      productName: this._productName,
      productSlug: this._productSlug,
      productImage: this._productImage,
      productSku: this._productSku,
      unitPrice: this._unitPrice,
      salePrice: this._salePrice,
      quantity: this._quantity,
      maxQuantity: this._maxQuantity,
      licenseType: this._licenseType,
      isDigital: this._isDigital,
      downloadSize: this._downloadSize,
      isAvailable: this._isAvailable,
      stockStatus: this._stockStatus,
      addedAt: this.formatDate(this._addedAt),
      updatedAt: this.formatDate(this._updatedAt),
    };
  }

  fromJson(data: Record<string, any>): void {
    this._id = data.id || this.generateId();
    this._productId = data.productId || 0;
    this._productName = data.productName || '';
    this._productSlug = data.productSlug || '';
    this._productImage = data.productImage;
    this._productSku = data.productSku;
    this._unitPrice = data.unitPrice || 0;
    this._salePrice = data.salePrice;
    this._quantity = data.quantity || 1;
    this._maxQuantity = data.maxQuantity;
    this._licenseType = data.licenseType;
    this._isDigital = data.isDigital !== undefined ? data.isDigital : true;
    this._downloadSize = data.downloadSize;
    this._isAvailable = data.isAvailable !== undefined ? data.isAvailable : true;
    this._stockStatus = data.stockStatus;
    this._addedAt = this.parseDate(data.addedAt) || new Date();
    this._updatedAt = this.parseDate(data.updatedAt);
  }

  // Business methods
  increaseQuantity(): boolean {
    if (this.canIncrease) {
      this._quantity++;
      this._updatedAt = new Date();
      return true;
    }
    return false;
  }

  decreaseQuantity(): boolean {
    if (this.canDecrease) {
      this._quantity--;
      this._updatedAt = new Date();
      return true;
    }
    return false;
  }

  setQuantity(quantity: number): boolean {
    if (quantity <= 0) return false;
    if (this._maxQuantity && quantity > this._maxQuantity) return false;
    
    this._quantity = quantity;
    this._updatedAt = new Date();
    return true;
  }

  updatePrice(unitPrice: number, salePrice?: number): void {
    this._unitPrice = unitPrice;
    this._salePrice = salePrice;
    this._updatedAt = new Date();
  }

  updateAvailability(isAvailable: boolean, stockStatus?: CartItemData['stockStatus']): void {
    this._isAvailable = isAvailable;
    this._stockStatus = stockStatus;
    this._updatedAt = new Date();
  }

  setMaxQuantity(maxQuantity: number): void {
    this._maxQuantity = maxQuantity;
    
    // Adjust current quantity if it exceeds the new max
    if (this._quantity > maxQuantity) {
      this._quantity = maxQuantity;
    }
    
    this._updatedAt = new Date();
  }

  // Utility methods
  private generateId(): string {
    return `cart_${this._productId}_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
  }

  isExpired(maxAgeHours: number = 24): boolean {
    const ageHours = (Date.now() - this._addedAt.getTime()) / (1000 * 60 * 60);
    return ageHours > maxAgeHours;
  }

  getAge(): { days: number; hours: number; minutes: number } {
    const ageMs = Date.now() - this._addedAt.getTime();
    const days = Math.floor(ageMs / (1000 * 60 * 60 * 24));
    const hours = Math.floor((ageMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((ageMs % (1000 * 60 * 60)) / (1000 * 60));
    
    return { days, hours, minutes };
  }

  getFormattedAge(): string {
    const { days, hours, minutes } = this.getAge();
    
    if (days > 0) {
      return `${days} day${days > 1 ? 's' : ''} ago`;
    }
    
    if (hours > 0) {
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    }
    
    return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
  }

  // Comparison methods
  isSameProduct(other: CartItem): boolean {
    return this._productId === other._productId && this._licenseType === other._licenseType;
  }

  canCombineWith(other: CartItem): boolean {
    return (
      this.isSameProduct(other) &&
      this._isAvailable &&
      other._isAvailable &&
      (!this._maxQuantity || this._quantity + other._quantity <= this._maxQuantity)
    );
  }

  combineWith(other: CartItem): boolean {
    if (!this.canCombineWith(other)) return false;
    
    this._quantity += other._quantity;
    this._updatedAt = new Date();
    
    // Update to the latest price if different
    if (other._unitPrice !== this._unitPrice || other._salePrice !== this._salePrice) {
      this._unitPrice = other._unitPrice;
      this._salePrice = other._salePrice;
    }
    
    return true;
  }

  // Convert to order item
  toOrderItem(): {
    productId: number;
    productName: string;
    productSku?: string;
    unitPrice: number;
    quantity: number;
    totalPrice: number;
  } {
    return {
      productId: this._productId,
      productName: this._productName,
      productSku: this._productSku,
      unitPrice: this.effectivePrice,
      quantity: this._quantity,
      totalPrice: this.totalPrice,
    };
  }

  // Search and filtering
  matchesSearch(query: string): boolean {
    const searchText = query.toLowerCase();
    return (
      this._productName.toLowerCase().includes(searchText) ||
      (this._productSku && this._productSku.toLowerCase().includes(searchText))
    );
  }

  matchesFilter(filter: { 
    licenseType?: string; 
    isDigital?: boolean; 
    isAvailable?: boolean;
    priceRange?: { min: number; max: number };
  }): boolean {
    if (filter.licenseType && this._licenseType !== filter.licenseType) return false;
    if (filter.isDigital !== undefined && this._isDigital !== filter.isDigital) return false;
    if (filter.isAvailable !== undefined && this._isAvailable !== filter.isAvailable) return false;
    
    if (filter.priceRange) {
      const price = this.effectivePrice;
      if (price < filter.priceRange.min || price > filter.priceRange.max) return false;
    }
    
    return true;
  }
}