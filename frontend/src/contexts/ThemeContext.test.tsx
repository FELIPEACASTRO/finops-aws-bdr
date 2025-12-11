import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { ThemeProvider, useTheme } from './ThemeContext';

// Test component to access theme context
function TestComponent() {
  const { theme, setTheme, effectiveTheme } = useTheme();
  return (
    <div>
      <span data-testid="theme">{theme}</span>
      <span data-testid="effective">{effectiveTheme}</span>
      <button onClick={() => setTheme('light')} data-testid="set-light">Light</button>
      <button onClick={() => setTheme('dark')} data-testid="set-dark">Dark</button>
      <button onClick={() => setTheme('system')} data-testid="set-system">System</button>
    </div>
  );
}

describe('ThemeContext', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  it('provides default dark theme', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId('theme')).toHaveTextContent('dark');
  });

  it('allows changing theme to light', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    act(() => {
      fireEvent.click(screen.getByTestId('set-light'));
    });

    expect(screen.getByTestId('theme')).toHaveTextContent('light');
  });

  it('allows changing theme to dark', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    act(() => {
      fireEvent.click(screen.getByTestId('set-light'));
    });

    act(() => {
      fireEvent.click(screen.getByTestId('set-dark'));
    });

    expect(screen.getByTestId('theme')).toHaveTextContent('dark');
  });

  it('persists theme to localStorage', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    act(() => {
      fireEvent.click(screen.getByTestId('set-light'));
    });

    expect(localStorage.getItem('finops-theme')).toBe('light');
  });

  it('throws error when useTheme is used outside provider', () => {
    const consoleError = console.error;
    console.error = () => {}; // Suppress error output

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useTheme must be used within a ThemeProvider');

    console.error = consoleError;
  });
});
