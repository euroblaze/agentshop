import { BaseModel } from './BaseModel';
import { CustomerAddress } from './Customer';

export interface OrderItem {
  id: number;
  productId: number;
  productName: string;
  productSku?: string;
  unitPrice: number;
  quantity: number;
  totalPrice: number;
  
  // Digital delivery
  licenseKey?: string;
  downloadUrl?: string;
  downloadExpiresAt?: Date;
  downloadCount: number;
  maxDownloads: number;
  
  // Status
  status: 'pending' | 'delivered' | 'expired';
  deliveredAt?: Date;
}

export interface Payment {
  id: number;
  orderId: number;
  method: 'credit_card' | 'paypal' | 'bank_transfer';
  processor: string;
  transactionId?: string;
  amount: number;
  currency: string;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  
  // Payment details
  paymentData?: Record<string, any>;
  
  // Timestamps
  processedAt?: Date;
  createdAt: Date;
}

export interface OrderData {
  id: number;
  orderNumber: string;
  customerId: number;
  
  // Order status
  status: 'pending' | 'processing' | 'completed' | 'cancelled' | 'refunded';
  paymentStatus: 'pending' | 'paid' | 'failed' | 'refunded';
  
  // Amounts
  subtotal: number;
  taxAmount: number;
  shippingAmount: number;
  discountAmount: number;
  totalAmount: number;
  currency: string;
  
  // Billing information
  billingAddress: CustomerAddress & {
    firstName: string;
    lastName: string;
    email: string;
    phone?: string;
  };
  
  // Shipping information (for physical goods)
  shippingAddress?: CustomerAddress & {
    firstName: string;
    lastName: string;
  };
  
  // Payment information
  paymentMethod?: string;
  paymentProcessor?: string;
  paymentTransactionId?: string;
  
  // Order metadata
  notes?: string;
  internalNotes?: string;
  source: 'web' | 'api' | 'admin';
  
  // Items and payments
  items: OrderItem[];
  payments: Payment[];
  
  // Timestamps
  processedAt?: Date;
  shippedAt?: Date;
  deliveredAt?: Date;
  cancelledAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export class Order extends BaseModel {
  private _orderNumber: string = '';
  private _customerId: number = 0;
  private _status: OrderData['status'] = 'pending';
  private _paymentStatus: OrderData['paymentStatus'] = 'pending';
  private _subtotal: number = 0;
  private _taxAmount: number = 0;
  private _shippingAmount: number = 0;
  private _discountAmount: number = 0;
  private _totalAmount: number = 0;
  private _currency: string = 'USD';
  private _billingAddress: OrderData['billingAddress'] = {
    firstName: '',
    lastName: '',
    email: '',
    line1: '',
    city: '',
    state: '',
    postalCode: '',
    country: ''
  };
  private _shippingAddress?: OrderData['shippingAddress'];
  private _paymentMethod?: string;
  private _paymentProcessor?: string;
  private _paymentTransactionId?: string;
  private _notes?: string;
  private _internalNotes?: string;
  private _source: OrderData['source'] = 'web';
  private _items: OrderItem[] = [];
  private _payments: Payment[] = [];
  private _processedAt?: Date;
  private _shippedAt?: Date;
  private _deliveredAt?: Date;
  private _cancelledAt?: Date;

  // Getters
  get orderNumber(): string { return this._orderNumber; }
  get customerId(): number { return this._customerId; }
  get status(): OrderData['status'] { return this._status; }
  get paymentStatus(): OrderData['paymentStatus'] { return this._paymentStatus; }
  get subtotal(): number { return this._subtotal; }
  get taxAmount(): number { return this._taxAmount; }
  get shippingAmount(): number { return this._shippingAmount; }
  get discountAmount(): number { return this._discountAmount; }
  get totalAmount(): number { return this._totalAmount; }
  get currency(): string { return this._currency; }
  get billingAddress(): OrderData['billingAddress'] { return this._billingAddress; }
  get shippingAddress(): OrderData['shippingAddress'] { return this._shippingAddress; }
  get paymentMethod(): string | undefined { return this._paymentMethod; }
  get paymentProcessor(): string | undefined { return this._paymentProcessor; }
  get paymentTransactionId(): string | undefined { return this._paymentTransactionId; }
  get notes(): string | undefined { return this._notes; }
  get internalNotes(): string | undefined { return this._internalNotes; }
  get source(): OrderData['source'] { return this._source; }
  get items(): OrderItem[] { return this._items; }
  get payments(): Payment[] { return this._payments; }
  get processedAt(): Date | undefined { return this._processedAt; }
  get shippedAt(): Date | undefined { return this._shippedAt; }
  get deliveredAt(): Date | undefined { return this._deliveredAt; }
  get cancelledAt(): Date | undefined { return this._cancelledAt; }

  // Setters
  set customerId(value: number) { this._customerId = value; }
  set notes(value: string | undefined) { this._notes = value; }

  // Computed properties
  get formattedOrderNumber(): string {
    return `#${this._orderNumber}`;
  }

  get formattedTotal(): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: this._currency
    }).format(this._totalAmount);
  }

  get formattedSubtotal(): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: this._currency
    }).format(this._subtotal);
  }

  get itemCount(): number {
    return this._items.reduce((sum, item) => sum + item.quantity, 0);
  }

  get uniqueItemCount(): number {
    return this._items.length;
  }

  get isPending(): boolean {
    return this._status === 'pending';
  }

  get isProcessing(): boolean {
    return this._status === 'processing';
  }

  get isCompleted(): boolean {
    return this._status === 'completed';
  }

  get isCancelled(): boolean {
    return this._status === 'cancelled';
  }

  get isRefunded(): boolean {
    return this._status === 'refunded';
  }

  get isPaid(): boolean {
    return this._paymentStatus === 'paid';
  }

  get canCancel(): boolean {
    return this._status === 'pending' || this._status === 'processing';
  }

  get canRefund(): boolean {
    return this._status === 'completed' && this._paymentStatus === 'paid';
  }

  get canReorder(): boolean {
    return this._items.length > 0;
  }

  get hasDigitalItems(): boolean {
    return this._items.some(item => item.downloadUrl);
  }

  get hasPhysicalItems(): boolean {
    return this._items.some(item => !item.downloadUrl);
  }

  get deliveryStatus(): 'pending' | 'partial' | 'delivered' {
    if (this._items.length === 0) return 'pending';
    
    const deliveredItems = this._items.filter(item => item.status === 'delivered');
    
    if (deliveredItems.length === 0) return 'pending';
    if (deliveredItems.length === this._items.length) return 'delivered';
    return 'partial';
  }

  get statusDisplayText(): string {
    switch (this._status) {
      case 'pending': return 'Pending';
      case 'processing': return 'Processing';
      case 'completed': return 'Completed';
      case 'cancelled': return 'Cancelled';
      case 'refunded': return 'Refunded';
      default: return 'Unknown';
    }
  }

  get paymentStatusDisplayText(): string {
    switch (this._paymentStatus) {
      case 'pending': return 'Payment Pending';
      case 'paid': return 'Paid';
      case 'failed': return 'Payment Failed';
      case 'refunded': return 'Refunded';
      default: return 'Unknown';
    }
  }

  get estimatedDeliveryDate(): Date | undefined {
    if (!this._processedAt) return undefined;
    
    // For digital products, delivery is immediate
    if (!this.hasPhysicalItems) {
      return this._processedAt;
    }
    
    // For physical products, add shipping time
    const deliveryDate = new Date(this._processedAt);
    deliveryDate.setDate(deliveryDate.getDate() + 3); // 3 days shipping
    return deliveryDate;
  }

  // Validation
  validate(): boolean {
    this.clearErrors();
    let isValid = true;

    if (!this.validateRequired(this._orderNumber, 'orderNumber')) {
      isValid = false;
    }

    if (!this.validateNumeric(this._customerId, 'customerId') || this._customerId <= 0) {
      this.addError('customerId', 'Valid customer ID is required');
      isValid = false;
    }

    if (this._totalAmount < 0) {
      this.addError('totalAmount', 'Total amount cannot be negative');
      isValid = false;
    }

    if (this._items.length === 0) {
      this.addError('items', 'Order must contain at least one item');
      isValid = false;
    }

    // Validate billing address
    if (!this.validateBillingAddress()) {
      isValid = false;
    }

    // Validate amounts
    if (!this.validateAmounts()) {
      isValid = false;
    }

    return isValid;
  }

  private validateBillingAddress(): boolean {
    let isValid = true;
    const { firstName, lastName, email, line1, city, state, postalCode, country } = this._billingAddress;

    if (!firstName.trim()) {
      this.addError('billingAddress.firstName', 'Billing first name is required');
      isValid = false;
    }

    if (!lastName.trim()) {
      this.addError('billingAddress.lastName', 'Billing last name is required');
      isValid = false;
    }

    if (!email.trim() || !this.validateEmail(email, 'billingAddress.email')) {
      isValid = false;
    }

    if (!line1.trim()) {
      this.addError('billingAddress.line1', 'Billing address is required');
      isValid = false;
    }

    if (!city.trim()) {
      this.addError('billingAddress.city', 'Billing city is required');
      isValid = false;
    }

    if (!state.trim()) {
      this.addError('billingAddress.state', 'Billing state is required');
      isValid = false;
    }

    if (!postalCode.trim()) {
      this.addError('billingAddress.postalCode', 'Billing postal code is required');
      isValid = false;
    }

    if (!country.trim()) {
      this.addError('billingAddress.country', 'Billing country is required');
      isValid = false;
    }

    return isValid;
  }

  private validateAmounts(): boolean {
    let isValid = true;

    const calculatedSubtotal = this._items.reduce((sum, item) => sum + item.totalPrice, 0);
    const calculatedTotal = calculatedSubtotal + this._taxAmount + this._shippingAmount - this._discountAmount;

    if (Math.abs(this._subtotal - calculatedSubtotal) > 0.01) {
      this.addError('subtotal', 'Subtotal does not match item totals');
      isValid = false;
    }

    if (Math.abs(this._totalAmount - calculatedTotal) > 0.01) {
      this.addError('totalAmount', 'Total amount calculation is incorrect');
      isValid = false;
    }

    return isValid;
  }

  // Serialization
  toJson(): Record<string, any> {
    return {
      id: this._id,
      orderNumber: this._orderNumber,
      customerId: this._customerId,
      status: this._status,
      paymentStatus: this._paymentStatus,
      subtotal: this._subtotal,
      taxAmount: this._taxAmount,
      shippingAmount: this._shippingAmount,
      discountAmount: this._discountAmount,
      totalAmount: this._totalAmount,
      currency: this._currency,
      billingAddress: this._billingAddress,
      shippingAddress: this._shippingAddress,
      paymentMethod: this._paymentMethod,
      paymentProcessor: this._paymentProcessor,
      paymentTransactionId: this._paymentTransactionId,
      notes: this._notes,
      internalNotes: this._internalNotes,
      source: this._source,
      items: this._items,
      payments: this._payments,
      processedAt: this.formatDate(this._processedAt),
      shippedAt: this.formatDate(this._shippedAt),
      deliveredAt: this.formatDate(this._deliveredAt),
      cancelledAt: this.formatDate(this._cancelledAt),
      createdAt: this.formatDate(this._createdAt),
      updatedAt: this.formatDate(this._updatedAt),
    };
  }

  fromJson(data: Record<string, any>): void {
    this._id = data.id;
    this._orderNumber = data.orderNumber || '';
    this._customerId = data.customerId || 0;
    this._status = data.status || 'pending';
    this._paymentStatus = data.paymentStatus || 'pending';
    this._subtotal = data.subtotal || 0;
    this._taxAmount = data.taxAmount || 0;
    this._shippingAmount = data.shippingAmount || 0;
    this._discountAmount = data.discountAmount || 0;
    this._totalAmount = data.totalAmount || 0;
    this._currency = data.currency || 'USD';
    this._billingAddress = { ...this._billingAddress, ...data.billingAddress };
    this._shippingAddress = data.shippingAddress;
    this._paymentMethod = data.paymentMethod;
    this._paymentProcessor = data.paymentProcessor;
    this._paymentTransactionId = data.paymentTransactionId;
    this._notes = data.notes;
    this._internalNotes = data.internalNotes;
    this._source = data.source || 'web';
    this._items = data.items || [];
    this._payments = data.payments || [];
    this._processedAt = this.parseDate(data.processedAt);
    this._shippedAt = this.parseDate(data.shippedAt);
    this._deliveredAt = this.parseDate(data.deliveredAt);
    this._cancelledAt = this.parseDate(data.cancelledAt);
    this._createdAt = this.parseDate(data.createdAt);
    this._updatedAt = this.parseDate(data.updatedAt);
  }

  // Business methods
  generateOrderNumber(): void {
    const timestamp = Date.now().toString();
    const random = Math.random().toString(36).substring(2, 8).toUpperCase();
    this._orderNumber = `${timestamp}-${random}`;
  }

  addItem(item: Omit<OrderItem, 'id'>): void {
    const newItem: OrderItem = {
      ...item,
      id: Date.now() + Math.random() // Simple ID generation
    };
    this._items.push(newItem);
    this.recalculateAmounts();
  }

  removeItem(itemId: number): void {
    this._items = this._items.filter(item => item.id !== itemId);
    this.recalculateAmounts();
  }

  updateItemQuantity(itemId: number, quantity: number): void {
    const item = this._items.find(i => i.id === itemId);
    if (item) {
      item.quantity = quantity;
      item.totalPrice = item.unitPrice * quantity;
      this.recalculateAmounts();
    }
  }

  private recalculateAmounts(): void {
    this._subtotal = this._items.reduce((sum, item) => sum + item.totalPrice, 0);
    this._totalAmount = this._subtotal + this._taxAmount + this._shippingAmount - this._discountAmount;
  }

  setTaxAmount(amount: number): void {
    this._taxAmount = amount;
    this.recalculateAmounts();
  }

  setShippingAmount(amount: number): void {
    this._shippingAmount = amount;
    this.recalculateAmounts();
  }

  setDiscountAmount(amount: number): void {
    this._discountAmount = amount;
    this.recalculateAmounts();
  }

  process(): void {
    this._status = 'processing';
    this._processedAt = new Date();
  }

  complete(): void {
    this._status = 'completed';
    this._deliveredAt = new Date();
    
    // Mark all items as delivered
    this._items.forEach(item => {
      if (item.status !== 'delivered') {
        item.status = 'delivered';
        item.deliveredAt = new Date();
      }
    });
  }

  cancel(reason?: string): void {
    this._status = 'cancelled';
    this._cancelledAt = new Date();
    if (reason && this._internalNotes) {
      this._internalNotes += `\nCancelled: ${reason}`;
    }
  }

  refund(): void {
    this._status = 'refunded';
    this._paymentStatus = 'refunded';
  }

  markAsPaid(transactionId?: string): void {
    this._paymentStatus = 'paid';
    if (transactionId) {
      this._paymentTransactionId = transactionId;
    }
  }

  // Item delivery methods
  deliverItem(itemId: number, downloadUrl?: string, licenseKey?: string): void {
    const item = this._items.find(i => i.id === itemId);
    if (item) {
      item.status = 'delivered';
      item.deliveredAt = new Date();
      if (downloadUrl) item.downloadUrl = downloadUrl;
      if (licenseKey) item.licenseKey = licenseKey;
      
      // Set download expiry (e.g., 30 days)
      if (downloadUrl) {
        const expiry = new Date();
        expiry.setDate(expiry.getDate() + 30);
        item.downloadExpiresAt = expiry;
      }
    }
  }

  incrementDownloadCount(itemId: number): boolean {
    const item = this._items.find(i => i.id === itemId);
    if (item && item.downloadCount < item.maxDownloads) {
      item.downloadCount++;
      return true;
    }
    return false;
  }

  getDownloadableItems(): OrderItem[] {
    return this._items.filter(item => 
      item.downloadUrl && 
      item.status === 'delivered' &&
      (!item.downloadExpiresAt || item.downloadExpiresAt > new Date()) &&
      item.downloadCount < item.maxDownloads
    );
  }

  // Reorder functionality
  getReorderItems(): Array<{ productId: number; quantity: number }> {
    return this._items.map(item => ({
      productId: item.productId,
      quantity: item.quantity
    }));
  }

  // Search and filtering
  matchesSearch(query: string): boolean {
    const searchText = query.toLowerCase();
    return (
      this._orderNumber.toLowerCase().includes(searchText) ||
      this._billingAddress.email.toLowerCase().includes(searchText) ||
      this._billingAddress.firstName.toLowerCase().includes(searchText) ||
      this._billingAddress.lastName.toLowerCase().includes(searchText) ||
      this._items.some(item => item.productName.toLowerCase().includes(searchText))
    );
  }
}