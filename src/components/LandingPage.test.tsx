import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import LandingPage from './LandingPage';
import { useAppState } from '../store';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock the global store hook
vi.mock('../store', () => ({
  useAppState: vi.fn(),
}));

describe('LandingPage Component Tests', () => {
  const mockSetCurrentTab = vi.fn();
  
  beforeEach(() => {
    vi.clearAllMocks();
    (useAppState as any).mockReturnValue({
      setCurrentTab: mockSetCurrentTab,
      plans: [
        {
          id: 'basic',
          name: 'Basic',
          description: 'Basic features',
          price_monthly: 10,
          price_yearly: 100,
          feature_limits: {
            ai_credits: 10,
            resume_limits: 2,
            interview_limits: 1,
            job_match_limits: 5,
          }
        }
      ],
      upgradeSubscription: vi.fn(),
    });
  });

  it('renders the LandingPage correctly', () => {
    render(<LandingPage />);
    expect(screen.getByText('JobCatalyst')).toBeInTheDocument();
    expect(screen.getByText('Log In')).toBeInTheDocument();
    expect(screen.getByText('Get Started Free')).toBeInTheDocument();
  });

  it('calls setCurrentTab when Log In is clicked', () => {
    render(<LandingPage />);
    const loginButton = screen.getByText('Log In');
    fireEvent.click(loginButton);
    expect(mockSetCurrentTab).toHaveBeenCalledWith('auth');
  });

  it('handles contact form submission', () => {
    render(<LandingPage />);
    
    const nameInput = screen.getByPlaceholderText('Alex Mercer');
    const emailInput = screen.getByPlaceholderText('alex@enterprise.com');
    const msgInput = screen.getByPlaceholderText('Describe your user volume or pricing inquiries...');
    const submitBtn = screen.getByText('Submit Contact Request');
    
    fireEvent.change(nameInput, { target: { value: 'Test User' } });
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(msgInput, { target: { value: 'This is a test message' } });
    
    fireEvent.click(submitBtn);
    
    expect(screen.getByText(/Successfully captured submission!/i)).toBeInTheDocument();
  });
});
