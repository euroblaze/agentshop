import { BaseApiService } from './BaseApiService';
import { Customer } from '../models/Customer';
import { Product } from '../models/Product';
import { Order } from '../models/Order';
import { CartItem } from '../models/CartItem';

// Product Service
export class ProductService extends BaseApiService<Product> {
  constructor() {
    super('/products', Product);
  }

  async getProducts(page: number = 1, limit: number = 20, filters?: Record<string, any>): Promise<{ products: Product[], total: number }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      ...filters
    });

    const response = await this.httpClient.get(`${this.basePath}?${params}`);
    return {
      products: response.data.map((item: any) => new Product(item)),
      total: response.pagination?.total || response.data.length
    };
  }

  async getFeaturedProducts(): Promise<Product[]> {
    const response = await this.httpClient.get(`${this.basePath}/featured`);
    return response.data.map((item: any) => new Product(item));
  }

  async searchProducts(query: string, filters?: Record<string, any>): Promise<Product[]> {
    const params = new URLSearchParams({
      q: query,
      ...filters
    });

    const response = await this.httpClient.get(`${this.basePath}/search?${params}`);
    return response.data.map((item: any) => new Product(item));
  }

  async getProductCategories(): Promise<string[]> {
    const response = await this.httpClient.get(`${this.basePath}/categories`);
    return response.data;
  }
}

// Customer Service
export class CustomerService extends BaseApiService<Customer> {
  constructor() {
    super('/customers', Customer);
  }

  async getCurrentCustomer(): Promise<Customer | null> {
    try {
      const response = await this.httpClient.get(`${this.basePath}/me`);
      return new Customer(response.data);
    } catch (error) {
      return null;
    }
  }

  async updateProfile(profileData: Partial<Customer>): Promise<Customer> {
    const response = await this.httpClient.put(`${this.basePath}/me`, profileData);
    return new Customer(response.data);
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<boolean> {
    try {
      await this.httpClient.post(`${this.basePath}/change-password`, {
        current_password: currentPassword,
        new_password: newPassword
      });
      return true;
    } catch (error) {
      return false;
    }
  }
}

// Order Service
export class OrderService extends BaseApiService<Order> {
  constructor() {
    super('/orders', Order);
  }

  async getCustomerOrders(page: number = 1, limit: number = 20): Promise<{ orders: Order[], total: number }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString()
    });

    const response = await this.httpClient.get(`${this.basePath}?${params}`);
    return {
      orders: response.data.map((item: any) => new Order(item)),
      total: response.pagination?.total || response.data.length
    };
  }

  async createOrder(orderData: any): Promise<Order> {
    const response = await this.httpClient.post(this.basePath, orderData);
    return new Order(response.data);
  }

  async getOrderById(orderId: string): Promise<Order | null> {
    try {
      const response = await this.httpClient.get(`${this.basePath}/${orderId}`);
      return new Order(response.data);
    } catch (error) {
      return null;
    }
  }

  async cancelOrder(orderId: string): Promise<boolean> {
    try {
      await this.httpClient.post(`${this.basePath}/${orderId}/cancel`);
      return true;
    } catch (error) {
      return false;
    }
  }
}

// Cart Service
export class CartService {
  private httpClient = BaseApiService.getHttpClient();
  private basePath = '/cart';

  async getCart(): Promise<{ items: CartItem[], subtotal: number, itemCount: number }> {
    try {
      const response = await this.httpClient.get(this.basePath);
      return {
        items: response.data.items.map((item: any) => new CartItem(item)),
        subtotal: response.data.subtotal || 0,
        itemCount: response.data.item_count || 0
      };
    } catch (error) {
      return { items: [], subtotal: 0, itemCount: 0 };
    }
  }

  async addToCart(productId: number, quantity: number = 1): Promise<CartItem | null> {
    try {
      const response = await this.httpClient.post(`${this.basePath}/items`, {
        product_id: productId,
        quantity
      });
      return new CartItem(response.data);
    } catch (error) {
      return null;
    }
  }

  async updateCartItem(itemId: number, quantity: number): Promise<CartItem | null> {
    try {
      const response = await this.httpClient.put(`${this.basePath}/items/${itemId}`, {
        quantity
      });
      return new CartItem(response.data);
    } catch (error) {
      return null;
    }
  }

  async removeFromCart(itemId: number): Promise<boolean> {
    try {
      await this.httpClient.delete(`${this.basePath}/items/${itemId}`);
      return true;
    } catch (error) {
      return false;
    }
  }

  async clearCart(): Promise<boolean> {
    try {
      await this.httpClient.delete(`${this.basePath}/clear`);
      return true;
    } catch (error) {
      return false;
    }
  }

  async getCartCount(): Promise<number> {
    try {
      const response = await this.httpClient.get(`${this.basePath}/count`);
      return response.data.count || 0;
    } catch (error) {
      return 0;
    }
  }
}

// Auth Service
export class AuthService {
  private httpClient = BaseApiService.getHttpClient();
  private basePath = '/auth';

  async login(email: string, password: string): Promise<{ token: string, customer: Customer } | null> {
    try {
      const response = await this.httpClient.post(`${this.basePath}/login`, {
        email,
        password
      });
      
      if (response.data.access_token) {
        // Store token in localStorage
        localStorage.setItem('auth_token', response.data.access_token);
        
        // Set token in HTTP client for future requests
        this.httpClient.setAuthToken(response.data.access_token);
        
        return {
          token: response.data.access_token,
          customer: new Customer(response.data.customer)
        };
      }
      return null;
    } catch (error) {
      return null;
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
      const response = await this.httpClient.post(`${this.basePath}/register`, {
        email: customerData.email,
        password: customerData.password,
        first_name: customerData.firstName,
        last_name: customerData.lastName,
        phone: customerData.phone
      });
      
      if (response.data.access_token) {
        localStorage.setItem('auth_token', response.data.access_token);
        this.httpClient.setAuthToken(response.data.access_token);
        
        return {
          token: response.data.access_token,
          customer: new Customer(response.data.customer)
        };
      }
      return null;
    } catch (error) {
      return null;
    }
  }

  async logout(): Promise<void> {
    try {
      await this.httpClient.post(`${this.basePath}/logout`);
    } catch (error) {
      // Continue with logout even if API call fails
    } finally {
      // Clear token from storage and HTTP client
      localStorage.removeItem('auth_token');
      this.httpClient.clearAuthToken();
    }
  }

  async forgotPassword(email: string): Promise<boolean> {
    try {
      await this.httpClient.post(`${this.basePath}/forgot-password`, { email });
      return true;
    } catch (error) {
      return false;
    }
  }

  async verifyEmail(token: string): Promise<boolean> {
    try {
      await this.httpClient.post(`${this.basePath}/verify-email`, { token });
      return true;
    } catch (error) {
      return false;
    }
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('auth_token');
  }

  getToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  // Initialize auth from stored token
  initializeAuth(): void {
    const token = this.getToken();
    if (token) {
      this.httpClient.setAuthToken(token);
    }
  }
}

// Export singleton instances
export const productService = new ProductService();
export const customerService = new CustomerService();
export const orderService = new OrderService();
export const cartService = new CartService();
export const authService = new AuthService();

// Initialize auth on module load
authService.initializeAuth();