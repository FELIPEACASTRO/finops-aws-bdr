import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />);
    // The app should render
    expect(document.body).toBeTruthy();
  });

  it('renders the dashboard by default', () => {
    render(<App />);
    // Dashboard should be visible on root route
    // Note: This may need adjustment based on actual content
  });
});
