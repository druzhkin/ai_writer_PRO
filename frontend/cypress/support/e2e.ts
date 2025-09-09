/**
 * Cypress support index file for global configuration and command imports
 */

// Import commands.js using ES2015 syntax:
import './commands'

// Import MSW for API mocking in E2E tests
import { server } from '../../src/mocks/server'

// Start MSW server before all tests
before(() => {
  server.listen({ onUnhandledRequest: 'error' })
})

// Reset MSW handlers after each test
afterEach(() => {
  server.resetHandlers()
})

// Stop MSW server after all tests
after(() => {
  server.close()
})

// Global configuration
Cypress.on('uncaught:exception', (err, runnable) => {
  // Prevent Cypress from failing on uncaught exceptions
  // that are not related to the test
  if (err.message.includes('ResizeObserver loop limit exceeded')) {
    return false
  }
  if (err.message.includes('Non-Error promise rejection captured')) {
    return false
  }
  return true
})

// Configure viewport
Cypress.config('viewportWidth', 1280)
Cypress.config('viewportHeight', 720)

// Configure default command timeout
Cypress.config('defaultCommandTimeout', 10000)

// Configure request timeout
Cypress.config('requestTimeout', 10000)

// Configure response timeout
Cypress.config('responseTimeout', 10000)

// Configure page load timeout
Cypress.config('pageLoadTimeout', 30000)

// Configure video recording
Cypress.config('video', true)

// Configure screenshot on failure
Cypress.config('screenshotOnRunFailure', true)

// Configure retry attempts
Cypress.config('retries', {
  runMode: 2,
  openMode: 0,
})

// Global beforeEach hook
beforeEach(() => {
  // Clear all cookies and local storage
  cy.clearCookies()
  cy.clearLocalStorage()
  cy.clearAllData()
  
  // Set default viewport
  cy.desktopViewport()
  
  // Mock common API endpoints
  cy.mockApi('GET', '/api/v1/users/me', { fixture: 'users.json' })
  cy.mockApi('GET', '/api/v1/organizations/', { fixture: 'organizations.json' })
  cy.mockApi('GET', '/api/v1/styles/', { fixture: 'styles.json' })
  cy.mockApi('GET', '/api/v1/content/', { fixture: 'content.json' })
})

// Global afterEach hook
afterEach(function () {
  // Take screenshot on failure using modern API
  if (this.currentTest?.state === 'failed') {
    cy.screenshot(`failed-${this.currentTest.title}`)
  }
  
  // Check for console errors
  cy.checkConsoleErrors()
})

// Custom error handling
Cypress.on('fail', (error, runnable) => {
  // Log additional information on test failure
  console.error('Test failed:', runnable.title)
  console.error('Error:', error.message)
  
  // You can add custom error reporting here
  // e.g., send to error tracking service
  
  throw error
})

// Performance monitoring
Cypress.on('test:after:run', (test, runnable) => {
  // Log test performance
  const duration = runnable.duration
  if (duration > 5000) {
    console.warn(`Slow test detected: ${test.title} took ${duration}ms`)
  }
})

// Network monitoring
let networkRequests: any[] = []

Cypress.on('window:before:load', (win) => {
  // Monitor network requests
  const originalFetch = win.fetch
  win.fetch = (...args) => {
    const startTime = Date.now()
    return originalFetch.apply(win, args).then((response) => {
      const endTime = Date.now()
      networkRequests.push({
        url: args[0],
        method: 'GET',
        duration: endTime - startTime,
        status: response.status,
      })
      return response
    })
  }
  
  // Monitor XMLHttpRequest
  const originalXHR = win.XMLHttpRequest
  win.XMLHttpRequest = class extends originalXHR {
    open(method: string, url: string) {
      this._method = method
      this._url = url
      this._startTime = Date.now()
      return super.open(method, url)
    }
    
    send(data?: any) {
      const originalOnLoad = this.onload
      this.onload = (event) => {
        const endTime = Date.now()
        networkRequests.push({
          url: this._url,
          method: this._method,
          duration: endTime - this._startTime,
          status: this.status,
        })
        if (originalOnLoad) {
          originalOnLoad.call(this, event)
        }
      }
      return super.send(data)
    }
  }
})

// Reset network monitoring after each test
afterEach(() => {
  networkRequests = []
})

// Accessibility testing setup
import 'cypress-axe'

// Custom accessibility commands
Cypress.Commands.add('checkA11y', (selector?: string) => {
  if (selector) {
    cy.get(selector).checkA11y()
  } else {
    cy.checkA11y()
  }
})

// Performance testing setup
Cypress.Commands.add('measurePerformance', (name: string, fn: () => void) => {
  const startTime = performance.now()
  fn()
  const endTime = performance.now()
  const duration = endTime - startTime
  
  cy.log(`Performance: ${name} took ${duration.toFixed(2)}ms`)
  
  // Assert performance requirements
  expect(duration).to.be.lessThan(1000) // Example: should complete within 1 second
})

// Custom assertions
Cypress.Commands.add('shouldHaveText', (selector: string, text: string) => {
  cy.get(selector).should('contain.text', text)
})

Cypress.Commands.add('shouldBeVisible', (selector: string) => {
  cy.get(selector).should('be.visible')
})

Cypress.Commands.add('shouldNotExist', (selector: string) => {
  cy.get(selector).should('not.exist')
})

// Extend Cypress namespace for custom commands
declare global {
  namespace Cypress {
    interface Chainable {
      checkA11y(selector?: string): Chainable<void>
      measurePerformance(name: string, fn: () => void): Chainable<void>
      shouldHaveText(selector: string, text: string): Chainable<void>
      shouldBeVisible(selector: string): Chainable<void>
      shouldNotExist(selector: string): Chainable<void>
    }
  }
}
