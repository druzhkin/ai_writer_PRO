/**
 * Cypress E2E tests for authentication flow
 */

describe('Authentication Flow', () => {
  beforeEach(() => {
    cy.visit('/login')
  })

  it('should display login form', () => {
    cy.get('form').should('be.visible')
    cy.get('input[type="email"]').should('be.visible')
    cy.get('input[type="password"]').should('be.visible')
    cy.get('button[type="submit"]').should('be.visible')
  })

  it('should show validation errors for empty fields', () => {
    cy.get('button[type="submit"]').click()
    
    cy.get('[data-testid="email-error"]').should('be.visible')
    cy.get('[data-testid="password-error"]').should('be.visible')
  })

  it('should show validation error for invalid email', () => {
    cy.get('input[type="email"]').type('invalid-email')
    cy.get('button[type="submit"]').click()
    
    cy.get('[data-testid="email-error"]').should('contain', 'Invalid email address')
  })

  it('should login with valid credentials', () => {
    cy.get('input[type="email"]').type('test@example.com')
    cy.get('input[type="password"]').type('password123')
    cy.get('button[type="submit"]').click()
    
    // Should redirect to dashboard
    cy.url().should('include', '/dashboard')
    cy.get('[data-testid="user-menu"]').should('be.visible')
  })

  it('should show error for invalid credentials', () => {
    cy.get('input[type="email"]').type('invalid@example.com')
    cy.get('input[type="password"]').type('wrongpassword')
    cy.get('button[type="submit"]').click()
    
    cy.get('[data-testid="error-message"]').should('contain', 'Invalid credentials')
  })

  it('should navigate to password reset page', () => {
    cy.get('a[href="/reset-password"]').click()
    cy.url().should('include', '/reset-password')
  })

  it('should navigate to registration page', () => {
    cy.get('a[href="/register"]').click()
    cy.url().should('include', '/register')
  })

  it('should handle OAuth login with Google', () => {
    cy.get('[data-testid="google-oauth-button"]').click()
    
    // Should redirect to OAuth provider
    cy.origin('https://accounts.google.com', () => {
      cy.url().should('include', 'accounts.google.com')
    })
  })

  it('should handle OAuth login with GitHub', () => {
    cy.get('[data-testid="github-oauth-button"]').click()
    
    // Should redirect to OAuth provider
    cy.origin('https://github.com', () => {
      cy.url().should('include', 'github.com')
    })
  })

  it('should logout successfully', () => {
    // First login
    cy.get('input[type="email"]').type('test@example.com')
    cy.get('input[type="password"]').type('password123')
    cy.get('button[type="submit"]').click()
    
    // Wait for redirect to dashboard
    cy.url().should('include', '/dashboard')
    
    // Logout
    cy.get('[data-testid="user-menu"]').click()
    cy.get('[data-testid="logout-button"]').click()
    
    // Should redirect to login page
    cy.url().should('include', '/login')
  })

  it('should persist login state on page refresh', () => {
    // Login
    cy.get('input[type="email"]').type('test@example.com')
    cy.get('input[type="password"]').type('password123')
    cy.get('button[type="submit"]').click()
    
    // Wait for redirect
    cy.url().should('include', '/dashboard')
    
    // Refresh page
    cy.reload()
    
    // Should still be logged in
    cy.url().should('include', '/dashboard')
    cy.get('[data-testid="user-menu"]').should('be.visible')
  })

  it('should redirect to dashboard if already logged in', () => {
    // Login first
    cy.get('input[type="email"]').type('test@example.com')
    cy.get('input[type="password"]').type('password123')
    cy.get('button[type="submit"]').click()
    
    // Wait for redirect
    cy.url().should('include', '/dashboard')
    
    // Try to visit login page again
    cy.visit('/login')
    
    // Should redirect back to dashboard
    cy.url().should('include', '/dashboard')
  })
})

describe('Registration Flow', () => {
  beforeEach(() => {
    cy.visit('/register')
  })

  it('should display registration form', () => {
    cy.get('form').should('be.visible')
    cy.get('input[name="email"]').should('be.visible')
    cy.get('input[name="username"]').should('be.visible')
    cy.get('input[name="password"]').should('be.visible')
    cy.get('input[name="confirmPassword"]').should('be.visible')
    cy.get('input[name="firstName"]').should('be.visible')
    cy.get('input[name="lastName"]').should('be.visible')
    cy.get('input[name="organizationName"]').should('be.visible')
  })

  it('should show validation errors for empty fields', () => {
    cy.get('button[type="submit"]').click()
    
    cy.get('[data-testid="email-error"]').should('be.visible')
    cy.get('[data-testid="username-error"]').should('be.visible')
    cy.get('[data-testid="password-error"]').should('be.visible')
    cy.get('[data-testid="firstName-error"]').should('be.visible')
    cy.get('[data-testid="lastName-error"]').should('be.visible')
    cy.get('[data-testid="organizationName-error"]').should('be.visible')
  })

  it('should show error for password mismatch', () => {
    cy.get('input[name="password"]').type('password123')
    cy.get('input[name="confirmPassword"]').type('differentpassword')
    cy.get('button[type="submit"]').click()
    
    cy.get('[data-testid="confirmPassword-error"]').should('contain', 'Passwords do not match')
  })

  it('should register new user successfully', () => {
    cy.get('input[name="email"]').type('newuser@example.com')
    cy.get('input[name="username"]').type('newuser')
    cy.get('input[name="password"]').type('password123')
    cy.get('input[name="confirmPassword"]').type('password123')
    cy.get('input[name="firstName"]').type('New')
    cy.get('input[name="lastName"]').type('User')
    cy.get('input[name="organizationName"]').type('New Organization')
    cy.get('button[type="submit"]').click()
    
    // Should redirect to dashboard
    cy.url().should('include', '/dashboard')
    cy.get('[data-testid="welcome-message"]').should('contain', 'Welcome, New')
  })

  it('should show error for existing email', () => {
    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="username"]').type('newuser')
    cy.get('input[name="password"]').type('password123')
    cy.get('input[name="confirmPassword"]').type('password123')
    cy.get('input[name="firstName"]').type('New')
    cy.get('input[name="lastName"]').type('User')
    cy.get('input[name="organizationName"]').type('New Organization')
    cy.get('button[type="submit"]').click()
    
    cy.get('[data-testid="error-message"]').should('contain', 'Email already exists')
  })
})

describe('Password Reset Flow', () => {
  beforeEach(() => {
    cy.visit('/reset-password')
  })

  it('should display password reset form', () => {
    cy.get('form').should('be.visible')
    cy.get('input[type="email"]').should('be.visible')
    cy.get('button[type="submit"]').should('be.visible')
  })

  it('should show validation error for empty email', () => {
    cy.get('button[type="submit"]').click()
    cy.get('[data-testid="email-error"]').should('be.visible')
  })

  it('should send password reset email', () => {
    cy.get('input[type="email"]').type('test@example.com')
    cy.get('button[type="submit"]').click()
    
    cy.get('[data-testid="success-message"]').should('contain', 'Password reset email sent')
  })

  it('should show error for non-existent email', () => {
    cy.get('input[type="email"]').type('nonexistent@example.com')
    cy.get('button[type="submit"]').click()
    
    cy.get('[data-testid="error-message"]').should('contain', 'Email not found')
  })
})
