/**
 * Navigation and routing logic manager
 * Handles programmatic navigation, route guards, and navigation state
 */

export interface RouteConfig {
  path: string;
  name: string;
  component?: React.ComponentType<any>;
  guard?: (to: RouteConfig, from?: RouteConfig) => boolean | Promise<boolean>;
  meta?: Record<string, any>;
  children?: RouteConfig[];
}

export interface NavigationGuard {
  name: string;
  guard: (to: RouteConfig, from?: RouteConfig) => boolean | Promise<boolean>;
  priority?: number;
}

export class RouteManager {
  private static instance: RouteManager;
  private routes: Map<string, RouteConfig> = new Map();
  private guards: NavigationGuard[] = [];
  private history: string[] = [];
  private currentRoute: RouteConfig | null = null;
  private navigationListeners: Set<(route: RouteConfig) => void> = new Set();

  private constructor() {
    this.initializeRoutes();
    this.setupBrowserNavigation();
  }

  static getInstance(): RouteManager {
    if (!RouteManager.instance) {
      RouteManager.instance = new RouteManager();
    }
    return RouteManager.instance;
  }

  // Route registration
  private initializeRoutes(): void {
    const routes: RouteConfig[] = [
      {
        path: '/',
        name: 'home',
        meta: { title: 'Home - AgentShop', public: true }
      },
      {
        path: '/products',
        name: 'products',
        meta: { title: 'Products - AgentShop', public: true }
      },
      {
        path: '/products/:id',
        name: 'product-detail',
        meta: { title: 'Product Details - AgentShop', public: true }
      },
      {
        path: '/search',
        name: 'search',
        meta: { title: 'Search Results - AgentShop', public: true }
      },
      {
        path: '/checkout',
        name: 'checkout',
        meta: { title: 'Checkout - AgentShop', public: true }
      },
      {
        path: '/order-confirmation/:orderId',
        name: 'order-confirmation',
        meta: { title: 'Order Confirmation - AgentShop', public: true }
      },
      {
        path: '/login',
        name: 'login',
        meta: { title: 'Login - AgentShop', public: true, authRedirect: true }
      },
      {
        path: '/register',
        name: 'register',
        meta: { title: 'Register - AgentShop', public: true, authRedirect: true }
      },
      {
        path: '/account',
        name: 'account',
        meta: { title: 'My Account - AgentShop', requiresAuth: true },
        guard: this.authGuard
      },
      {
        path: '/account/orders',
        name: 'account-orders',
        meta: { title: 'Order History - AgentShop', requiresAuth: true },
        guard: this.authGuard
      },
      {
        path: '/account/profile',
        name: 'account-profile',
        meta: { title: 'Profile - AgentShop', requiresAuth: true },
        guard: this.authGuard
      },
      {
        path: '/account/support',
        name: 'account-support',
        meta: { title: 'Support - AgentShop', requiresAuth: true },
        guard: this.authGuard
      },
    ];

    routes.forEach(route => {
      this.routes.set(route.name, route);
    });
  }

  // Navigation methods
  navigate(routeName: string, params?: Record<string, string>): Promise<boolean> {
    const route = this.routes.get(routeName);
    if (!route) {
      console.error(`Route '${routeName}' not found`);
      return Promise.resolve(false);
    }

    return this.navigateToRoute(route, params);
  }

  navigateToPath(path: string): Promise<boolean> {
    const route = this.findRouteByPath(path);
    if (!route) {
      console.error(`No route found for path '${path}'`);
      return Promise.resolve(false);
    }

    return this.navigateToRoute(route);
  }

  private async navigateToRoute(route: RouteConfig, params?: Record<string, string>): Promise<boolean> {
    // Run navigation guards
    const canNavigate = await this.runGuards(route, this.currentRoute || undefined);
    if (!canNavigate) {
      return false;
    }

    // Build URL with parameters
    let url = route.path;
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url = url.replace(`:${key}`, value);
      });
    }

    // Update browser history
    window.history.pushState({ route: route.name }, '', url);
    
    // Update internal state
    this.addToHistory(url);
    this.currentRoute = route;
    
    // Update document title
    if (route.meta?.title) {
      document.title = route.meta.title;
    }

    // Notify listeners
    this.notifyNavigationListeners(route);

    return true;
  }

  replace(routeName: string, params?: Record<string, string>): Promise<boolean> {
    const route = this.routes.get(routeName);
    if (!route) {
      console.error(`Route '${routeName}' not found`);
      return Promise.resolve(false);
    }

    return this.replaceRoute(route, params);
  }

  private async replaceRoute(route: RouteConfig, params?: Record<string, string>): Promise<boolean> {
    // Run navigation guards
    const canNavigate = await this.runGuards(route, this.currentRoute || undefined);
    if (!canNavigate) {
      return false;
    }

    // Build URL with parameters
    let url = route.path;
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url = url.replace(`:${key}`, value);
      });
    }

    // Replace browser history
    window.history.replaceState({ route: route.name }, '', url);
    
    // Update internal state (don't add to history for replace)
    this.currentRoute = route;
    
    // Update document title
    if (route.meta?.title) {
      document.title = route.meta.title;
    }

    // Notify listeners
    this.notifyNavigationListeners(route);

    return true;
  }

  go(delta: number): void {
    window.history.go(delta);
  }

  back(): void {
    window.history.back();
  }

  forward(): void {
    window.history.forward();
  }

  // Guard management
  addGlobalGuard(guard: NavigationGuard): void {
    this.guards.push(guard);
    this.guards.sort((a, b) => (b.priority || 0) - (a.priority || 0));
  }

  removeGlobalGuard(guardName: string): void {
    this.guards = this.guards.filter(g => g.name !== guardName);
  }

  private async runGuards(to: RouteConfig, from?: RouteConfig): Promise<boolean> {
    // Run route-specific guard first
    if (to.guard) {
      const result = await to.guard(to, from);
      if (!result) return false;
    }

    // Run global guards
    for (const guard of this.guards) {
      const result = await guard.guard(to, from);
      if (!result) return false;
    }

    return true;
  }

  // Built-in guards
  private authGuard = (to: RouteConfig, from?: RouteConfig): boolean => {
    // This would check authentication state from StateManager
    const isAuthenticated = this.isAuthenticated();
    
    if (!isAuthenticated && to.meta?.requiresAuth) {
      // Redirect to login with return URL
      this.navigate('login', { returnUrl: to.path });
      return false;
    }

    // If authenticated and trying to access auth pages, redirect to account
    if (isAuthenticated && to.meta?.authRedirect) {
      this.navigate('account');
      return false;
    }

    return true;
  };

  // Utility methods
  private findRouteByPath(path: string): RouteConfig | null {
    for (const route of this.routes.values()) {
      if (this.matchPath(route.path, path)) {
        return route;
      }
    }
    return null;
  }

  private matchPath(routePath: string, actualPath: string): boolean {
    // Simple path matching - convert :param to regex
    const pattern = routePath.replace(/:([^/]+)/g, '([^/]+)');
    const regex = new RegExp(`^${pattern}$`);
    return regex.test(actualPath);
  }

  extractParams(routePath: string, actualPath: string): Record<string, string> {
    const params: Record<string, string> = {};
    const routeParts = routePath.split('/');
    const actualParts = actualPath.split('/');

    for (let i = 0; i < routeParts.length; i++) {
      const routePart = routeParts[i];
      const actualPart = actualParts[i];

      if (routePart.startsWith(':')) {
        const paramName = routePart.slice(1);
        params[paramName] = actualPart;
      }
    }

    return params;
  }

  getCurrentRoute(): RouteConfig | null {
    return this.currentRoute;
  }

  getHistory(): string[] {
    return [...this.history];
  }

  canGoBack(): boolean {
    return this.history.length > 1;
  }

  // Browser navigation setup
  private setupBrowserNavigation(): void {
    window.addEventListener('popstate', (event) => {
      const path = window.location.pathname;
      const route = this.findRouteByPath(path);
      
      if (route) {
        this.currentRoute = route;
        this.notifyNavigationListeners(route);
      }
    });

    // Handle initial route
    const currentPath = window.location.pathname;
    const currentRoute = this.findRouteByPath(currentPath);
    if (currentRoute) {
      this.currentRoute = currentRoute;
    }
  }

  // History management
  private addToHistory(path: string): void {
    this.history.push(path);
    
    // Limit history size
    if (this.history.length > 100) {
      this.history.shift();
    }
  }

  // Listeners
  onNavigate(listener: (route: RouteConfig) => void): () => void {
    this.navigationListeners.add(listener);
    
    return () => {
      this.navigationListeners.delete(listener);
    };
  }

  private notifyNavigationListeners(route: RouteConfig): void {
    this.navigationListeners.forEach(listener => {
      try {
        listener(route);
      } catch (error) {
        console.error('Navigation listener error:', error);
      }
    });
  }

  // Route generation helpers
  generateUrl(routeName: string, params?: Record<string, string>): string {
    const route = this.routes.get(routeName);
    if (!route) {
      console.error(`Route '${routeName}' not found`);
      return '/';
    }

    let url = route.path;
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url = url.replace(`:${key}`, value);
      });
    }

    return url;
  }

  // Authentication check (would integrate with StateManager)
  private isAuthenticated(): boolean {
    // This would check the actual authentication state
    // For now, return false as placeholder
    return false;
  }

  // Debug methods
  debug(): void {
    console.log('Current Route:', this.currentRoute);
    console.log('History:', this.history);
    console.log('Registered Routes:', Array.from(this.routes.values()));
    console.log('Guards:', this.guards);
  }

  getAllRoutes(): RouteConfig[] {
    return Array.from(this.routes.values());
  }
}

// Export singleton instance
export const routeManager = RouteManager.getInstance();