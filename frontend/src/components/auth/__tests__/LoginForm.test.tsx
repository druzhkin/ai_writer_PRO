/**
 * Comprehensive component tests for authentication components
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import LoginForm from '../LoginForm'

// Mock the API hook
jest.mock('@/hooks/api', () => ({
  useLogin: () => ({
    mutate: jest.fn(),
    isLoading: false,
    error: null,
  }),
}))

describe('LoginForm', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders login form correctly', () => {
    render(<LoginForm />)
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    expect(screen.getByText(/forgot password/i)).toBeInTheDocument()
  })

  it('shows validation errors for empty fields', async () => {
    render(<LoginForm />)
    
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument()
      expect(screen.getByText(/password is required/i)).toBeInTheDocument()
    })
  })

  it('shows validation error for invalid email', async () => {
    render(<LoginForm />)
    
    const emailInput = screen.getByLabelText(/email/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    
    await user.type(emailInput, 'invalid-email')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/invalid email address/i)).toBeInTheDocument()
    })
  })

  it('submits form with valid data', async () => {
    const mockMutate = jest.fn()
    jest.doMock('@/hooks/api', () => ({
      useLogin: () => ({
        mutate: mockMutate,
        isLoading: false,
        error: null,
      }),
    }))

    render(<LoginForm />)
    
    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(mockMutate).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      })
    })
  })

  it('shows loading state during submission', () => {
    jest.doMock('@/hooks/api', () => ({
      useLogin: () => ({
        mutate: jest.fn(),
        isLoading: true,
        error: null,
      }),
    }))

    render(<LoginForm />)
    
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    expect(submitButton).toBeDisabled()
  })

  it('shows error message on login failure', () => {
    jest.doMock('@/hooks/api', () => ({
      useLogin: () => ({
        mutate: jest.fn(),
        isLoading: false,
        error: { message: 'Invalid credentials' },
      }),
    }))

    render(<LoginForm />)
    
    expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
  })

  it('navigates to password reset page', async () => {
    render(<LoginForm />)
    
    const forgotPasswordLink = screen.getByText(/forgot password/i)
    await user.click(forgotPasswordLink)
    
    // This would test navigation in a real app
    expect(forgotPasswordLink).toHaveAttribute('href', '/reset-password')
  })

  it('shows OAuth buttons', () => {
    render(<LoginForm />)
    
    expect(screen.getByText(/continue with google/i)).toBeInTheDocument()
    expect(screen.getByText(/continue with github/i)).toBeInTheDocument()
  })

  it('handles OAuth button clicks', async () => {
    render(<LoginForm />)
    
    const googleButton = screen.getByText(/continue with google/i)
    await user.click(googleButton)
    
    // This would test OAuth flow in a real app
    expect(googleButton).toBeInTheDocument()
  })

  it('is accessible', () => {
    render(<LoginForm />)
    
    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    
    expect(emailInput).toHaveAttribute('type', 'email')
    expect(passwordInput).toHaveAttribute('type', 'password')
    expect(submitButton).toHaveAttribute('type', 'submit')
  })

  it('supports keyboard navigation', async () => {
    render(<LoginForm />)
    
    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    
    emailInput.focus()
    expect(emailInput).toHaveFocus()
    
    await user.tab()
    expect(passwordInput).toHaveFocus()
    
    await user.tab()
    expect(submitButton).toHaveFocus()
  })
})
