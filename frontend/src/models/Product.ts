import { BaseModel } from './BaseModel';

export interface ProductCategory {
  id: number;
  name: string;
  slug: string;
  description?: string;
}

export interface ProductReview {
  id: number;
  customerId: number;
  customerName: string;
  rating: number; // 1-5
  comment?: string;
  isVerified: boolean;
  thumbsUp: number;
  thumbsDown: number;
  userThumb?: 'up' | 'down' | null;
  createdAt: Date;
}

export interface ProductInquiry {
  id: number;
  customerId?: number;
  customerName: string;
  customerEmail: string;
  question: string;
  answer?: string;
  isPublic: boolean;
  createdAt: Date;
  answeredAt?: Date;
}

export interface ProductFile {
  id: string;
  name: string;
  url: string;
  size: number;
  type: string;
}

export interface ProductData {
  id: number;
  name: string;
  slug: string;
  shortDescription?: string;
  fullDescription?: string;
  
  // Categorization
  categoryId?: number;
  category?: ProductCategory;
  tags: string[];
  
  // Pricing
  price: number;
  priceType: 'fixed' | 'inquiry' | 'free' | 'subscription';
  salePrice?: number;
  saleStart?: Date;
  saleEnd?: Date;
  
  // Status
  status: 'draft' | 'active' | 'inactive' | 'archived';
  featured: boolean;
  
  // Media
  featuredImage?: string;
  galleryImages: string[];
  demoVideoUrl?: string;
  
  // Product details
  sku?: string;
  weight?: number;
  dimensions?: {
    length: number;
    width: number;
    height: number;
    unit: string;
  };
  
  // SEO
  metaTitle?: string;
  metaDescription?: string;
  metaKeywords?: string;
  
  // Stats
  viewCount: number;
  downloadCount: number;
  ratingAverage?: number;
  ratingCount: number;
  
  // Digital product specifics
  downloadFiles: ProductFile[];
  licenseType?: 'personal' | 'commercial' | 'enterprise';
  systemRequirements?: {
    os: string[];
    ram: string;
    storage: string;
    other: string[];
  };
  
  // AI/LLM specific
  supportedProviders: string[];
  modelRequirements?: {
    minTokens: number;
    maxTokens: number;
    requiredCapabilities: string[];
  };
  
  // Relations
  reviews: ProductReview[];
  inquiries: ProductInquiry[];
  
  // Timestamps
  createdAt: Date;
  updatedAt: Date;
}

export class Product extends BaseModel {
  private _name: string = '';
  private _slug: string = '';
  private _shortDescription?: string;
  private _fullDescription?: string;
  private _categoryId?: number;
  private _category?: ProductCategory;
  private _tags: string[] = [];
  private _price: number = 0;
  private _priceType: ProductData['priceType'] = 'fixed';
  private _salePrice?: number;
  private _saleStart?: Date;
  private _saleEnd?: Date;
  private _status: ProductData['status'] = 'draft';
  private _featured: boolean = false;
  private _featuredImage?: string;
  private _galleryImages: string[] = [];
  private _demoVideoUrl?: string;
  private _sku?: string;
  private _weight?: number;
  private _dimensions?: ProductData['dimensions'];
  private _metaTitle?: string;
  private _metaDescription?: string;
  private _metaKeywords?: string;
  private _viewCount: number = 0;
  private _downloadCount: number = 0;
  private _ratingAverage?: number;
  private _ratingCount: number = 0;
  private _downloadFiles: ProductFile[] = [];
  private _licenseType?: ProductData['licenseType'];
  private _systemRequirements?: ProductData['systemRequirements'];
  private _supportedProviders: string[] = [];
  private _modelRequirements?: ProductData['modelRequirements'];
  private _reviews: ProductReview[] = [];
  private _inquiries: ProductInquiry[] = [];

  // Getters
  get name(): string { return this._name; }
  get slug(): string { return this._slug; }
  get shortDescription(): string | undefined { return this._shortDescription; }
  get fullDescription(): string | undefined { return this._fullDescription; }
  get categoryId(): number | undefined { return this._categoryId; }
  get category(): ProductCategory | undefined { return this._category; }
  get tags(): string[] { return this._tags; }
  get price(): number { return this._price; }
  get priceType(): ProductData['priceType'] { return this._priceType; }
  get salePrice(): number | undefined { return this._salePrice; }
  get saleStart(): Date | undefined { return this._saleStart; }
  get saleEnd(): Date | undefined { return this._saleEnd; }
  get status(): ProductData['status'] { return this._status; }
  get featured(): boolean { return this._featured; }
  get featuredImage(): string | undefined { return this._featuredImage; }
  get galleryImages(): string[] { return this._galleryImages; }
  get demoVideoUrl(): string | undefined { return this._demoVideoUrl; }
  get sku(): string | undefined { return this._sku; }
  get weight(): number | undefined { return this._weight; }
  get dimensions(): ProductData['dimensions'] { return this._dimensions; }
  get metaTitle(): string | undefined { return this._metaTitle; }
  get metaDescription(): string | undefined { return this._metaDescription; }
  get metaKeywords(): string | undefined { return this._metaKeywords; }
  get viewCount(): number { return this._viewCount; }
  get downloadCount(): number { return this._downloadCount; }
  get ratingAverage(): number | undefined { return this._ratingAverage; }
  get ratingCount(): number { return this._ratingCount; }
  get downloadFiles(): ProductFile[] { return this._downloadFiles; }
  get licenseType(): ProductData['licenseType'] { return this._licenseType; }
  get systemRequirements(): ProductData['systemRequirements'] { return this._systemRequirements; }
  get supportedProviders(): string[] { return this._supportedProviders; }
  get modelRequirements(): ProductData['modelRequirements'] { return this._modelRequirements; }
  get reviews(): ProductReview[] { return this._reviews; }
  get inquiries(): ProductInquiry[] { return this._inquiries; }

  // Setters
  set name(value: string) { this._name = value; }
  set shortDescription(value: string | undefined) { this._shortDescription = value; }
  set fullDescription(value: string | undefined) { this._fullDescription = value; }
  set price(value: number) { this._price = value; }
  set salePrice(value: number | undefined) { this._salePrice = value; }

  // Computed properties
  get displayPrice(): number {
    if (this.isOnSale) {
      return this._salePrice || this._price;
    }
    return this._price;
  }

  get isOnSale(): boolean {
    if (!this._salePrice || this._salePrice >= this._price) return false;
    
    const now = new Date();
    
    if (this._saleStart && now < this._saleStart) return false;
    if (this._saleEnd && now > this._saleEnd) return false;
    
    return true;
  }

  get discountPercentage(): number {
    if (!this.isOnSale || !this._salePrice) return 0;
    return Math.round(((this._price - this._salePrice) / this._price) * 100);
  }

  get isAvailable(): boolean {
    return this._status === 'active';
  }

  get hasReviews(): boolean {
    return this._reviews.length > 0;
  }

  get averageRating(): number {
    return this._ratingAverage || 0;
  }

  get formattedPrice(): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(this.displayPrice);
  }

  get priceDisplay(): string {
    switch (this._priceType) {
      case 'free':
        return 'Free';
      case 'inquiry':
        return 'Contact for pricing';
      case 'subscription':
        return `${this.formattedPrice}/month`;
      default:
        return this.formattedPrice;
    }
  }

  // Validation
  validate(): boolean {
    this.clearErrors();
    let isValid = true;

    if (!this.validateRequired(this._name, 'name')) {
      isValid = false;
    }

    if (!this.validateRequired(this._slug, 'slug')) {
      isValid = false;
    }

    if (this._price < 0) {
      this.addError('price', 'Price must be greater than or equal to 0');
      isValid = false;
    }

    if (this._salePrice && this._salePrice < 0) {
      this.addError('salePrice', 'Sale price must be greater than or equal to 0');
      isValid = false;
    }

    if (this._shortDescription && this._shortDescription.length > 500) {
      this.addError('shortDescription', 'Short description must be 500 characters or less');
      isValid = false;
    }

    return isValid;
  }

  // Serialization
  toJson(): Record<string, any> {
    return {
      id: this._id,
      name: this._name,
      slug: this._slug,
      shortDescription: this._shortDescription,
      fullDescription: this._fullDescription,
      categoryId: this._categoryId,
      category: this._category,
      tags: this._tags,
      price: this._price,
      priceType: this._priceType,
      salePrice: this._salePrice,
      saleStart: this.formatDate(this._saleStart),
      saleEnd: this.formatDate(this._saleEnd),
      status: this._status,
      featured: this._featured,
      featuredImage: this._featuredImage,
      galleryImages: this._galleryImages,
      demoVideoUrl: this._demoVideoUrl,
      sku: this._sku,
      weight: this._weight,
      dimensions: this._dimensions,
      metaTitle: this._metaTitle,
      metaDescription: this._metaDescription,
      metaKeywords: this._metaKeywords,
      viewCount: this._viewCount,
      downloadCount: this._downloadCount,
      ratingAverage: this._ratingAverage,
      ratingCount: this._ratingCount,
      downloadFiles: this._downloadFiles,
      licenseType: this._licenseType,
      systemRequirements: this._systemRequirements,
      supportedProviders: this._supportedProviders,
      modelRequirements: this._modelRequirements,
      reviews: this._reviews,
      inquiries: this._inquiries,
      createdAt: this.formatDate(this._createdAt),
      updatedAt: this.formatDate(this._updatedAt),
    };
  }

  fromJson(data: Record<string, any>): void {
    this._id = data.id;
    this._name = data.name || '';
    this._slug = data.slug || '';
    this._shortDescription = data.shortDescription;
    this._fullDescription = data.fullDescription;
    this._categoryId = data.categoryId;
    this._category = data.category;
    this._tags = data.tags || [];
    this._price = data.price || 0;
    this._priceType = data.priceType || 'fixed';
    this._salePrice = data.salePrice;
    this._saleStart = this.parseDate(data.saleStart);
    this._saleEnd = this.parseDate(data.saleEnd);
    this._status = data.status || 'draft';
    this._featured = data.featured || false;
    this._featuredImage = data.featuredImage;
    this._galleryImages = data.galleryImages || [];
    this._demoVideoUrl = data.demoVideoUrl;
    this._sku = data.sku;
    this._weight = data.weight;
    this._dimensions = data.dimensions;
    this._metaTitle = data.metaTitle;
    this._metaDescription = data.metaDescription;
    this._metaKeywords = data.metaKeywords;
    this._viewCount = data.viewCount || 0;
    this._downloadCount = data.downloadCount || 0;
    this._ratingAverage = data.ratingAverage;
    this._ratingCount = data.ratingCount || 0;
    this._downloadFiles = data.downloadFiles || [];
    this._licenseType = data.licenseType;
    this._systemRequirements = data.systemRequirements;
    this._supportedProviders = data.supportedProviders || [];
    this._modelRequirements = data.modelRequirements;
    this._reviews = data.reviews || [];
    this._inquiries = data.inquiries || [];
    this._createdAt = this.parseDate(data.createdAt);
    this._updatedAt = this.parseDate(data.updatedAt);
  }

  // Business methods
  addReview(review: ProductReview): void {
    this._reviews.push(review);
    this.updateRatingStats();
  }

  removeReview(reviewId: number): void {
    this._reviews = this._reviews.filter(r => r.id !== reviewId);
    this.updateRatingStats();
  }

  private updateRatingStats(): void {
    if (this._reviews.length === 0) {
      this._ratingAverage = undefined;
      this._ratingCount = 0;
      return;
    }

    const total = this._reviews.reduce((sum, review) => sum + review.rating, 0);
    this._ratingAverage = total / this._reviews.length;
    this._ratingCount = this._reviews.length;
  }

  addInquiry(inquiry: ProductInquiry): void {
    this._inquiries.push(inquiry);
  }

  getPublicInquiries(): ProductInquiry[] {
    return this._inquiries.filter(i => i.isPublic);
  }

  incrementViewCount(): void {
    this._viewCount++;
  }

  incrementDownloadCount(): void {
    this._downloadCount++;
  }

  // Search and filtering helpers
  matchesSearch(query: string): boolean {
    const searchText = query.toLowerCase();
    return (
      this._name.toLowerCase().includes(searchText) ||
      (this._shortDescription?.toLowerCase().includes(searchText)) ||
      this._tags.some(tag => tag.toLowerCase().includes(searchText)) ||
      (this._category?.name.toLowerCase().includes(searchText))
    );
  }

  matchesFilters(filters: Record<string, any>): boolean {
    // Price range filter
    if (filters.minPrice && this.displayPrice < filters.minPrice) return false;
    if (filters.maxPrice && this.displayPrice > filters.maxPrice) return false;

    // Category filter
    if (filters.categoryId && this._categoryId !== filters.categoryId) return false;

    // Provider filter
    if (filters.provider && !this._supportedProviders.includes(filters.provider)) return false;

    // License type filter
    if (filters.licenseType && this._licenseType !== filters.licenseType) return false;

    // Rating filter
    if (filters.minRating && (!this._ratingAverage || this._ratingAverage < filters.minRating)) return false;

    // Featured filter
    if (filters.featured && !this._featured) return false;

    return true;
  }
}