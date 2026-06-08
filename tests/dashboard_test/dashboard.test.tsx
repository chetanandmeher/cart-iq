/**
 * Dashboard smoke and routing tests.
 * Uses React Testing Library + Vitest to verify the app renders
 * and routes work correctly.
 */
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../../apps/dashboard/src/App';

// Mock the child page components to isolate routing logic
vi.mock('../../apps/dashboard/src/features/analytics/DashboardPage', () => ({
  default: () => <div data-testid="dashboard-page">Dashboard Page</div>,
}));

vi.mock('../../apps/dashboard/src/features/infra/InfraPage', () => ({
  default: () => <div data-testid="infra-page">Infra Page</div>,
}));

vi.mock('../../apps/dashboard/src/layout/Sidebar', () => ({
  default: () => <nav data-testid="sidebar">Sidebar</nav>,
}));

vi.mock('../../apps/dashboard/src/layout/TopBar', () => ({
  default: () => <header data-testid="topbar">TopBar</header>,
}));

describe('App Component', () => {
  beforeEach(() => {
    // Reset URL to root before each test
    window.history.pushState({}, '', '/');
  });

  it('renders without crashing', () => {
    render(<App />);
    // If render doesn't throw, the app loaded successfully
  });

  it('renders the Sidebar', () => {
    render(<App />);
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
  });

  it('renders the TopBar', () => {
    render(<App />);
    expect(screen.getByTestId('topbar')).toBeInTheDocument();
  });

  it('renders the DashboardPage on root route', () => {
    render(<App />);
    expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
  });

  it('renders the InfraPage on /infra route', () => {
    window.history.pushState({}, '', '/infra');
    render(<App />);
    expect(screen.getByTestId('infra-page')).toBeInTheDocument();
  });

  it('redirects unknown routes to dashboard', () => {
    window.history.pushState({}, '', '/unknown-route');
    render(<App />);
    expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
  });
});
