/**
 * Toast Component Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, act, renderHook } from '@testing-library/react';
import { Toast, ToastProvider, useToast } from '@/components/ui/Toast';

describe('Toast Component', () => {
  it('should render success toast', () => {
    render(
      <Toast
        message="Success message"
        type="success"
        isVisible={true}
        onClose={() => {}}
      />
    );

    expect(screen.getByText('Success message')).toBeInTheDocument();
    const container = screen.getByText('Success message').closest('div');
    expect(container).toHaveClass('bg-green-500');
  });

  it('should render error toast', () => {
    render(
      <Toast
        message="Error message"
        type="error"
        isVisible={true}
        onClose={() => {}}
      />
    );

    expect(screen.getByText('Error message')).toBeInTheDocument();
    const container = screen.getByText('Error message').closest('div');
    expect(container).toHaveClass('bg-red-500');
  });

  it('should render warning toast', () => {
    render(
      <Toast
        message="Warning message"
        type="warning"
        isVisible={true}
        onClose={() => {}}
      />
    );

    expect(screen.getByText('Warning message')).toBeInTheDocument();
    const container = screen.getByText('Warning message').closest('div');
    expect(container).toHaveClass('bg-yellow-500');
  });

  it('should render info toast', () => {
    render(
      <Toast
        message="Info message"
        type="info"
        isVisible={true}
        onClose={() => {}}
      />
    );

    expect(screen.getByText('Info message')).toBeInTheDocument();
    const container = screen.getByText('Info message').closest('div');
    expect(container).toHaveClass('bg-blue-500');
  });

  it('should call onClose when close button is clicked', () => {
    const mockOnClose = vi.fn();

    render(
      <Toast
        message="Test message"
        type="info"
        isVisible={true}
        onClose={mockOnClose}
      />
    );

    const closeButton = screen.getByRole('button');
    closeButton.click();

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should not render when isVisible is false', () => {
    const { container } = render(
      <Toast
        message="Hidden message"
        type="info"
        isVisible={false}
        onClose={() => {}}
      />
    );

    expect(container.firstChild).toHaveClass('opacity-0');
  });
});

describe('ToastProvider and useToast', () => {
  it('should show toast through context', () => {
    const TestComponent = () => {
      const { showToast } = useToast();

      return (
        <button onClick={() => showToast('Test message', 'success')}>
          Show Toast
        </button>
      );
    };

    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const button = screen.getByText('Show Toast');
    act(() => {
      button.click();
    });

    expect(screen.getByText('Test message')).toBeInTheDocument();
  });

  it('should auto-hide toast after duration', async () => {
    vi.useFakeTimers();

    const TestComponent = () => {
      const { showToast } = useToast();

      return (
        <button onClick={() => showToast('Auto hide', 'info', 3000)}>
          Show Toast
        </button>
      );
    };

    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const button = screen.getByText('Show Toast');
    act(() => {
      button.click();
    });

    expect(screen.getByText('Auto hide')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    const toastElement = screen.getByText('Auto hide').closest('div')?.parentElement;
    expect(toastElement).toHaveClass('opacity-0');

    vi.useRealTimers();
  });

  it('should show multiple toasts sequentially', () => {
    const TestComponent = () => {
      const { showToast } = useToast();

      return (
        <>
          <button onClick={() => showToast('First', 'info')}>First</button>
          <button onClick={() => showToast('Second', 'success')}>Second</button>
        </>
      );
    };

    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const firstButton = screen.getByText('First');
    const secondButton = screen.getByText('Second');

    act(() => {
      firstButton.click();
    });

    expect(screen.getByText('First')).toBeInTheDocument();

    act(() => {
      secondButton.click();
    });

    // Second toast should replace the first one
    expect(screen.queryByText('First')).not.toBeInTheDocument();
    expect(screen.getByText('Second')).toBeInTheDocument();
  });

  it('should handle hideToast function', () => {
    const TestComponent = () => {
      const { showToast, hideToast } = useToast();

      return (
        <>
          <button onClick={() => showToast('Test', 'info')}>Show</button>
          <button onClick={hideToast}>Hide</button>
        </>
      );
    };

    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const showButton = screen.getByText('Show');
    const hideButton = screen.getByText('Hide');

    act(() => {
      showButton.click();
    });

    expect(screen.getByText('Test')).toBeInTheDocument();

    act(() => {
      hideButton.click();
    });

    const toastElement = screen.getByText('Test').closest('div')?.parentElement;
    expect(toastElement).toHaveClass('opacity-0');
  });
});

describe('useToast hook outside provider', () => {
  it('should throw error when used outside ToastProvider', () => {
    const TestComponent = () => {
      useToast();
      return <div>Test</div>;
    };

    // Suppress console.error for this test
    const originalError = console.error;
    console.error = vi.fn();

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useToast must be used within a ToastProvider');

    console.error = originalError;
  });
});