/**
 * Global application state management
 * Provides centralized state management for the entire application
 */

export interface AppState {
  // Authentication state
  auth: {
    isAuthenticated: boolean;
    user: any | null;
    token: string | null;
  };
  
  // Shopping cart state
  cart: {
    items: any[];
    total: number;
    count: number;
  };
  
  // UI state
  ui: {
    isLoading: boolean;
    notifications: Notification[];
    modals: Record<string, boolean>;
    sidebar: {
      isOpen: boolean;
    };
  };
  
  // Product state
  products: {
    currentProduct: any | null;
    searchResults: any[];
    filters: Record<string, any>;
  };
  
  // Configuration
  config: {
    apiUrl: string;
    theme: 'light' | 'dark';
    language: string;
  };
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
  action?: {
    label: string;
    handler: () => void;
  };
}

type StateListener = (state: AppState) => void;
type StateUpdater = (state: AppState) => Partial<AppState>;

export class StateManager {
  private static instance: StateManager;
  private state: AppState;
  private listeners: Set<StateListener> = new Set();
  private history: AppState[] = [];
  private maxHistorySize = 50;

  private constructor() {
    this.state = this.getInitialState();
    this.loadPersistedState();
  }

  static getInstance(): StateManager {
    if (!StateManager.instance) {
      StateManager.instance = new StateManager();
    }
    return StateManager.instance;
  }

  private getInitialState(): AppState {
    return {
      auth: {
        isAuthenticated: false,
        user: null,
        token: null,
      },
      cart: {
        items: [],
        total: 0,
        count: 0,
      },
      ui: {
        isLoading: false,
        notifications: [],
        modals: {},
        sidebar: {
          isOpen: false,
        },
      },
      products: {
        currentProduct: null,
        searchResults: [],
        filters: {},
      },
      config: {
        apiUrl: import.meta.env.VITE_API_URL || '/api',
        theme: 'light',
        language: 'en',
      },
    };
  }

  // State access
  getState(): AppState {
    return { ...this.state };
  }

  getStateSlice<K extends keyof AppState>(key: K): AppState[K] {
    return { ...this.state[key] };
  }

  // State updates
  setState(updater: Partial<AppState> | StateUpdater): void {
    // Save current state to history
    this.addToHistory();

    // Update state
    const updates = typeof updater === 'function' ? updater(this.state) : updater;
    this.state = this.mergeState(this.state, updates);

    // Persist critical state
    this.persistState();

    // Notify listeners
    this.notifyListeners();
  }

  updateStateSlice<K extends keyof AppState>(
    key: K,
    updates: Partial<AppState[K]> | ((slice: AppState[K]) => Partial<AppState[K]>)
  ): void {
    const currentSlice = this.state[key];
    const sliceUpdates = typeof updates === 'function' ? updates(currentSlice) : updates;
    
    this.setState({
      [key]: { ...currentSlice, ...sliceUpdates }
    } as Partial<AppState>);
  }

  // Authentication methods
  setAuthenticated(user: any, token: string): void {
    this.updateStateSlice('auth', {
      isAuthenticated: true,
      user,
      token,
    });
  }

  setUnauthenticated(): void {
    this.updateStateSlice('auth', {
      isAuthenticated: false,
      user: null,
      token: null,
    });
  }

  // Cart methods
  addToCart(item: any): void {
    const currentCart = this.state.cart;
    const existingItem = currentCart.items.find(i => i.id === item.id);
    
    let updatedItems;
    if (existingItem) {
      updatedItems = currentCart.items.map(i =>
        i.id === item.id ? { ...i, quantity: i.quantity + 1 } : i
      );
    } else {
      updatedItems = [...currentCart.items, { ...item, quantity: 1 }];
    }

    const total = updatedItems.reduce((sum, i) => sum + (i.price * i.quantity), 0);
    const count = updatedItems.reduce((sum, i) => sum + i.quantity, 0);

    this.updateStateSlice('cart', {
      items: updatedItems,
      total,
      count,
    });
  }

  removeFromCart(itemId: string | number): void {
    const currentCart = this.state.cart;
    const updatedItems = currentCart.items.filter(i => i.id !== itemId);
    const total = updatedItems.reduce((sum, i) => sum + (i.price * i.quantity), 0);
    const count = updatedItems.reduce((sum, i) => sum + i.quantity, 0);

    this.updateStateSlice('cart', {
      items: updatedItems,
      total,
      count,
    });
  }

  updateCartItem(itemId: string | number, quantity: number): void {
    if (quantity <= 0) {
      this.removeFromCart(itemId);
      return;
    }

    const currentCart = this.state.cart;
    const updatedItems = currentCart.items.map(i =>
      i.id === itemId ? { ...i, quantity } : i
    );
    const total = updatedItems.reduce((sum, i) => sum + (i.price * i.quantity), 0);
    const count = updatedItems.reduce((sum, i) => sum + i.quantity, 0);

    this.updateStateSlice('cart', {
      items: updatedItems,
      total,
      count,
    });
  }

  clearCart(): void {
    this.updateStateSlice('cart', {
      items: [],
      total: 0,
      count: 0,
    });
  }

  // Notification methods
  addNotification(notification: Omit<Notification, 'id'>): string {
    const id = Date.now().toString();
    const newNotification: Notification = { id, ...notification };
    
    this.updateStateSlice('ui', {
      notifications: [...this.state.ui.notifications, newNotification]
    });

    // Auto-remove after duration
    if (notification.duration) {
      setTimeout(() => {
        this.removeNotification(id);
      }, notification.duration);
    }

    return id;
  }

  removeNotification(id: string): void {
    this.updateStateSlice('ui', {
      notifications: this.state.ui.notifications.filter(n => n.id !== id)
    });
  }

  clearNotifications(): void {
    this.updateStateSlice('ui', {
      notifications: []
    });
  }

  // Modal methods
  openModal(modalId: string): void {
    this.updateStateSlice('ui', {
      modals: { ...this.state.ui.modals, [modalId]: true }
    });
  }

  closeModal(modalId: string): void {
    this.updateStateSlice('ui', {
      modals: { ...this.state.ui.modals, [modalId]: false }
    });
  }

  // Loading state
  setLoading(loading: boolean): void {
    this.updateStateSlice('ui', { isLoading: loading });
  }

  // Listeners
  subscribe(listener: StateListener): () => void {
    this.listeners.add(listener);
    
    // Return unsubscribe function
    return () => {
      this.listeners.delete(listener);
    };
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => {
      try {
        listener(this.state);
      } catch (error) {
        console.error('State listener error:', error);
      }
    });
  }

  // History management
  private addToHistory(): void {
    this.history.push({ ...this.state });
    
    // Limit history size
    if (this.history.length > this.maxHistorySize) {
      this.history.shift();
    }
  }

  undo(): boolean {
    if (this.history.length === 0) return false;
    
    const previousState = this.history.pop();
    if (previousState) {
      this.state = previousState;
      this.notifyListeners();
      return true;
    }
    return false;
  }

  canUndo(): boolean {
    return this.history.length > 0;
  }

  // Persistence
  private persistState(): void {
    try {
      const persistedState = {
        auth: this.state.auth,
        cart: this.state.cart,
        config: this.state.config,
      };
      localStorage.setItem('agentshop_state', JSON.stringify(persistedState));
    } catch (error) {
      console.warn('Failed to persist state:', error);
    }
  }

  private loadPersistedState(): void {
    try {
      const persistedState = localStorage.getItem('agentshop_state');
      if (persistedState) {
        const parsed = JSON.parse(persistedState);
        this.state = this.mergeState(this.state, parsed);
      }
    } catch (error) {
      console.warn('Failed to load persisted state:', error);
    }
  }

  clearPersistedState(): void {
    localStorage.removeItem('agentshop_state');
  }

  // Utility methods
  private mergeState(current: AppState, updates: Partial<AppState>): AppState {
    const merged = { ...current };
    
    for (const key in updates) {
      if (updates.hasOwnProperty(key)) {
        const updateValue = updates[key as keyof AppState];
        if (updateValue && typeof updateValue === 'object' && !Array.isArray(updateValue)) {
          merged[key as keyof AppState] = { 
            ...current[key as keyof AppState], 
            ...updateValue 
          } as any;
        } else {
          merged[key as keyof AppState] = updateValue as any;
        }
      }
    }
    
    return merged;
  }

  // Debug methods
  debug(): void {
    console.log('Current State:', this.state);
    console.log('History Length:', this.history.length);
    console.log('Listeners Count:', this.listeners.size);
  }

  reset(): void {
    this.state = this.getInitialState();
    this.history = [];
    this.clearPersistedState();
    this.notifyListeners();
  }
}

// Export singleton instance
export const stateManager = StateManager.getInstance();