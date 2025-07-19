import React, { Component, ErrorInfo, ReactNode } from 'react';

/**
 * Abstract base component class with common lifecycle methods and utilities
 */
export interface BaseComponentProps {
  className?: string;
  testId?: string;
  children?: ReactNode;
}

export interface BaseComponentState {
  isLoading: boolean;
  error: string | null;
  hasError: boolean;
}

export abstract class BaseComponent<
  P extends BaseComponentProps = BaseComponentProps,
  S extends BaseComponentState = BaseComponentState
> extends Component<P, S> {
  
  protected mounted: boolean = false;

  constructor(props: P) {
    super(props);
    this.state = this.getInitialState();
  }

  // Abstract methods that child classes can override
  protected abstract getInitialState(): S;
  
  // Lifecycle methods
  componentDidMount(): void {
    this.mounted = true;
    this.onMount();
  }

  componentWillUnmount(): void {
    this.mounted = false;
    this.onUnmount();
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('Component Error:', error, errorInfo);
    this.handleError(error.message);
  }

  // Hook methods that child classes can override
  protected onMount(): void {
    // Override in child classes
  }

  protected onUnmount(): void {
    // Override in child classes
  }

  // Common state management methods
  protected setLoading(loading: boolean): void {
    if (this.mounted) {
      this.setState({ isLoading: loading } as Partial<S>);
    }
  }

  protected setError(error: string | null): void {
    if (this.mounted) {
      this.setState({ 
        error, 
        hasError: !!error,
        isLoading: false 
      } as Partial<S>);
    }
  }

  protected clearError(): void {
    this.setError(null);
  }

  protected handleError(error: string | Error): void {
    const errorMessage = error instanceof Error ? error.message : error;
    this.setError(errorMessage);
  }

  // Async operation wrapper
  protected async executeAsync<T>(
    operation: () => Promise<T>,
    onSuccess?: (result: T) => void,
    onError?: (error: Error) => void
  ): Promise<T | null> {
    try {
      this.setLoading(true);
      this.clearError();
      
      const result = await operation();
      
      if (onSuccess) {
        onSuccess(result);
      }
      
      return result;
    } catch (error) {
      const errorObj = error instanceof Error ? error : new Error(String(error));
      
      if (onError) {
        onError(errorObj);
      } else {
        this.handleError(errorObj);
      }
      
      return null;
    } finally {
      this.setLoading(false);
    }
  }

  // Safe state update (only if component is mounted)
  protected safeSetState(updater: Partial<S> | ((prevState: S) => Partial<S>)): void {
    if (this.mounted) {
      if (typeof updater === 'function') {
        this.setState(updater);
      } else {
        this.setState(updater);
      }
    }
  }

  // Utility methods
  protected getClassName(...classNames: (string | undefined | null | false)[]): string {
    return classNames.filter(Boolean).join(' ');
  }

  protected getTestId(suffix?: string): string {
    const { testId } = this.props;
    if (!testId) return '';
    return suffix ? `${testId}-${suffix}` : testId;
  }

  // Debounced function helper
  protected debounce<T extends (...args: any[]) => any>(
    func: T,
    delay: number
  ): (...args: Parameters<T>) => void {
    let timeoutId: NodeJS.Timeout;
    
    return (...args: Parameters<T>) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
  }

  // Throttled function helper
  protected throttle<T extends (...args: any[]) => any>(
    func: T,
    delay: number
  ): (...args: Parameters<T>) => void {
    let lastCall = 0;
    
    return (...args: Parameters<T>) => {
      const now = Date.now();
      if (now - lastCall >= delay) {
        lastCall = now;
        func.apply(this, args);
      }
    };
  }

  // Event handling helpers
  protected preventDefault = (event: React.SyntheticEvent): void => {
    event.preventDefault();
  };

  protected stopPropagation = (event: React.SyntheticEvent): void => {
    event.stopPropagation();
  };

  protected preventDefaultAndStop = (event: React.SyntheticEvent): void => {
    event.preventDefault();
    event.stopPropagation();
  };

  // Form handling helpers
  protected handleInputChange = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>): void => {
    const { name, value, type } = event.target;
    const inputValue = type === 'checkbox' ? (event.target as HTMLInputElement).checked : value;
    
    this.setState({
      [name]: inputValue
    } as Partial<S>);
  };

  protected handleFormSubmit = (event: React.FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    this.onSubmit();
  };

  // Override in child classes for form submission
  protected onSubmit(): void {
    // Override in child classes
  }

  // Validation helpers
  protected validateRequired(value: any, fieldName: string): boolean {
    if (value === null || value === undefined || value === '') {
      this.setError(`${fieldName} is required`);
      return false;
    }
    return true;
  }

  protected validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      this.setError('Please enter a valid email address');
      return false;
    }
    return true;
  }

  // Loading and error rendering helpers
  protected renderLoading(): ReactNode {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading...</span>
      </div>
    );
  }

  protected renderError(): ReactNode {
    const { error } = this.state;
    if (!error) return null;

    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
        <div className="flex">
          <div className="text-red-800">
            <p className="text-sm font-medium">Error</p>
            <p className="text-sm">{error}</p>
          </div>
          <button
            onClick={() => this.clearError()}
            className="ml-auto text-red-600 hover:text-red-800"
          >
            ×
          </button>
        </div>
      </div>
    );
  }

  // Conditional rendering helper
  protected renderIf(condition: boolean, element: ReactNode): ReactNode {
    return condition ? element : null;
  }

  // Array rendering helper
  protected renderList<T>(
    items: T[],
    renderItem: (item: T, index: number) => ReactNode,
    emptyMessage: string = 'No items found'
  ): ReactNode {
    if (items.length === 0) {
      return <div className="text-gray-500 text-center py-4">{emptyMessage}</div>;
    }

    return items.map(renderItem);
  }
}