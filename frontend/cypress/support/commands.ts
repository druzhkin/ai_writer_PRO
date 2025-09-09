/**
 * Cypress support commands for common test operations
 */

// Custom command for login
Cypress.Commands.add('login', (email: string, password: string) => {
  cy.session([email, password], () => {
    cy.visit('/login')
    cy.get('input[type="email"]').type(email)
    cy.get('input[type="password"]').type(password)
    cy.get('button[type="submit"]').click()
    cy.url().should('include', '/dashboard')
  })
})

// Custom command for API mocking
Cypress.Commands.add('mockApi', (method: string, url: string, response: any) => {
  cy.intercept(method, url, response)
})

// Custom command for waiting for API calls
Cypress.Commands.add('waitForApi', (alias: string) => {
  cy.wait(alias)
})

// Custom command for clearing all data
Cypress.Commands.add('clearAllData', () => {
  cy.window().then((win) => {
    win.localStorage.clear()
    win.sessionStorage.clear()
  })
})

// Custom command for setting user data
Cypress.Commands.add('setUserData', (userData: any) => {
  cy.window().then((win) => {
    win.localStorage.setItem('user', JSON.stringify(userData))
  })
})

// Custom command for getting user data
Cypress.Commands.add('getUserData', () => {
  return cy.window().then((win) => {
    const userData = win.localStorage.getItem('user')
    return userData ? JSON.parse(userData) : null
  })
})

// Custom command for file upload
Cypress.Commands.add('uploadFile', (selector: string, filePath: string) => {
  cy.get(selector).selectFile(filePath)
})

// Custom command for drag and drop
Cypress.Commands.add('dragAndDrop', (sourceSelector: string, targetSelector: string) => {
  cy.get(sourceSelector).trigger('dragstart')
  cy.get(targetSelector).trigger('drop')
})

// Custom command for waiting for element to be visible
Cypress.Commands.add('waitForVisible', (selector: string, timeout = 10000) => {
  cy.get(selector, { timeout }).should('be.visible')
})

// Custom command for waiting for element to not exist
Cypress.Commands.add('waitForNotExist', (selector: string, timeout = 10000) => {
  cy.get(selector, { timeout }).should('not.exist')
})

// Custom command for checking if element exists
Cypress.Commands.add('elementExists', (selector: string) => {
  return cy.get('body').then(($body) => {
    return $body.find(selector).length > 0
  })
})

// Custom command for scrolling to element
Cypress.Commands.add('scrollToElement', (selector: string) => {
  cy.get(selector).scrollIntoView()
})

// Custom command for taking screenshot with custom name
Cypress.Commands.add('takeScreenshot', (name: string) => {
  cy.screenshot(name, { capture: 'viewport' })
})

// Custom command for checking accessibility
Cypress.Commands.add('checkA11y', (selector?: string) => {
  if (selector) {
    cy.get(selector).checkA11y()
  } else {
    cy.checkA11y()
  }
})

// Custom command for waiting for network to be idle
Cypress.Commands.add('waitForNetworkIdle', (timeout = 2000) => {
  cy.window().then((win) => {
    return new Cypress.Promise((resolve) => {
      let idleTimer: NodeJS.Timeout
      const resetTimer = () => {
        clearTimeout(idleTimer)
        idleTimer = setTimeout(resolve, timeout)
      }
      
      // Listen for network requests
      win.addEventListener('fetch', resetTimer)
      win.addEventListener('xhr', resetTimer)
      
      // Start the timer
      resetTimer()
    })
  })
})

// Custom command for mocking date
Cypress.Commands.add('mockDate', (date: string | Date) => {
  const mockDate = new Date(date)
  cy.clock(mockDate.getTime())
})

// Custom command for restoring date
Cypress.Commands.add('restoreDate', () => {
  cy.clock().then((clock) => {
    clock.restore()
  })
})

// Custom command for setting viewport size
Cypress.Commands.add('setViewport', (width: number, height: number) => {
  cy.viewport(width, height)
})

// Custom command for mobile viewport
Cypress.Commands.add('mobileViewport', () => {
  cy.viewport(375, 667)
})

// Custom command for tablet viewport
Cypress.Commands.add('tabletViewport', () => {
  cy.viewport(768, 1024)
})

// Custom command for desktop viewport
Cypress.Commands.add('desktopViewport', () => {
  cy.viewport(1920, 1080)
})

// Custom command for checking if element is in viewport
Cypress.Commands.add('isInViewport', (selector: string) => {
  cy.get(selector).then(($el) => {
    const rect = $el[0].getBoundingClientRect()
    const isInViewport = (
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <= Cypress.config('viewportHeight') &&
      rect.right <= Cypress.config('viewportWidth')
    )
    expect(isInViewport).to.be.true
  })
})

// Custom command for waiting for animation to complete
Cypress.Commands.add('waitForAnimation', (selector: string) => {
  cy.get(selector).should('have.css', 'animation-duration', '0s')
})

// Custom command for checking console errors
Cypress.Commands.add('checkConsoleErrors', () => {
  cy.window().then((win) => {
    const consoleErrors: string[] = []
    const originalError = win.console.error
    
    win.console.error = (...args) => {
      consoleErrors.push(args.join(' '))
      originalError.apply(win.console, args)
    }
    
    cy.wrap(consoleErrors).should('have.length', 0)
  })
})

// Custom command for performance testing
Cypress.Commands.add('measurePerformance', (name: string) => {
  cy.window().then((win) => {
    const startTime = performance.now()
    
    return cy.wrap(null).then(() => {
      const endTime = performance.now()
      const duration = endTime - startTime
      
      cy.log(`Performance: ${name} took ${duration.toFixed(2)}ms`)
      
      // You can add assertions here based on performance requirements
      expect(duration).to.be.lessThan(1000) // Example: should complete within 1 second
    })
  })
})

// Extend Cypress namespace
declare global {
  namespace Cypress {
    interface Chainable {
      login(email: string, password: string): Chainable<void>
      mockApi(method: string, url: string, response: any): Chainable<void>
      waitForApi(alias: string): Chainable<void>
      clearAllData(): Chainable<void>
      setUserData(userData: any): Chainable<void>
      getUserData(): Chainable<any>
      uploadFile(selector: string, filePath: string): Chainable<void>
      dragAndDrop(sourceSelector: string, targetSelector: string): Chainable<void>
      waitForVisible(selector: string, timeout?: number): Chainable<void>
      waitForNotExist(selector: string, timeout?: number): Chainable<void>
      elementExists(selector: string): Chainable<boolean>
      scrollToElement(selector: string): Chainable<void>
      takeScreenshot(name: string): Chainable<void>
      checkA11y(selector?: string): Chainable<void>
      waitForNetworkIdle(timeout?: number): Chainable<void>
      mockDate(date: string | Date): Chainable<void>
      restoreDate(): Chainable<void>
      setViewport(width: number, height: number): Chainable<void>
      mobileViewport(): Chainable<void>
      tabletViewport(): Chainable<void>
      desktopViewport(): Chainable<void>
      isInViewport(selector: string): Chainable<void>
      waitForAnimation(selector: string): Chainable<void>
      checkConsoleErrors(): Chainable<void>
      measurePerformance(name: string): Chainable<void>
    }
  }
}
