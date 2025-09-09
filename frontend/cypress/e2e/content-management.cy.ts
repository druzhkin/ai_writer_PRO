/**
 * Cypress E2E tests for content management
 */

describe('Content Management', () => {
  beforeEach(() => {
    // Login before each test
    cy.login('test@example.com', 'password123')
    cy.visit('/dashboard/content')
  })

  it('should display content list page', () => {
    cy.get('[data-testid="content-list"]').should('be.visible')
    cy.get('[data-testid="new-content-button"]').should('be.visible')
  })

  it('should navigate to new content page', () => {
    cy.get('[data-testid="new-content-button"]').click()
    cy.url().should('include', '/dashboard/content/new')
  })

  it('should create new content', () => {
    cy.get('[data-testid="new-content-button"]').click()
    
    // Fill out the form
    cy.get('input[name="title"]').type('Test Article')
    cy.get('textarea[name="brief"]').type('This is a test brief for content generation')
    cy.get('input[name="targetWords"]').type('1000')
    cy.get('select[name="styleProfile"]').select('Test Style')
    
    // Submit the form
    cy.get('button[type="submit"]').click()
    
    // Should redirect to content list or show success message
    cy.get('[data-testid="success-message"]').should('contain', 'Content generation started')
  })

  it('should show validation errors for empty required fields', () => {
    cy.get('[data-testid="new-content-button"]').click()
    cy.get('button[type="submit"]').click()
    
    cy.get('[data-testid="title-error"]').should('be.visible')
    cy.get('[data-testid="brief-error"]').should('be.visible')
    cy.get('[data-testid="targetWords-error"]').should('be.visible')
    cy.get('[data-testid="styleProfile-error"]').should('be.visible')
  })

  it('should edit existing content', () => {
    // Assuming there's existing content
    cy.get('[data-testid="content-item"]').first().click()
    cy.url().should('include', '/dashboard/content/')
    
    // Click edit button
    cy.get('[data-testid="edit-button"]').click()
    
    // Update title
    cy.get('input[name="title"]').clear().type('Updated Article Title')
    cy.get('button[type="submit"]').click()
    
    // Should show success message
    cy.get('[data-testid="success-message"]').should('contain', 'Content updated')
  })

  it('should delete content', () => {
    // Assuming there's existing content
    cy.get('[data-testid="content-item"]').first().click()
    cy.url().should('include', '/dashboard/content/')
    
    // Click delete button
    cy.get('[data-testid="delete-button"]').click()
    
    // Confirm deletion in modal
    cy.get('[data-testid="confirm-delete-button"]').click()
    
    // Should redirect to content list
    cy.url().should('include', '/dashboard/content')
    cy.get('[data-testid="success-message"]').should('contain', 'Content deleted')
  })

  it('should filter content by status', () => {
    cy.get('[data-testid="status-filter"]').select('completed')
    cy.get('[data-testid="content-item"]').should('have.length.greaterThan', 0)
    
    cy.get('[data-testid="status-filter"]').select('pending')
    cy.get('[data-testid="content-item"]').should('have.length', 0)
  })

  it('should search content by title', () => {
    cy.get('[data-testid="search-input"]').type('Test Article')
    cy.get('[data-testid="search-button"]').click()
    
    cy.get('[data-testid="content-item"]').should('contain', 'Test Article')
  })

  it('should paginate through content list', () => {
    // Assuming there are multiple pages of content
    cy.get('[data-testid="pagination"]').should('be.visible')
    cy.get('[data-testid="next-page-button"]').click()
    
    cy.url().should('include', 'page=2')
  })
})

describe('Style Management', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'password123')
    cy.visit('/dashboard/styles')
  })

  it('should display style profiles list', () => {
    cy.get('[data-testid="styles-list"]').should('be.visible')
    cy.get('[data-testid="new-style-button"]').should('be.visible')
  })

  it('should create new style profile', () => {
    cy.get('[data-testid="new-style-button"]').click()
    
    // Fill out the form
    cy.get('input[name="name"]').type('New Style')
    cy.get('textarea[name="description"]').type('A new style profile for testing')
    cy.get('select[name="tone"]').select('casual')
    cy.get('select[name="voice"]').select('friendly')
    cy.get('select[name="targetAudience"]').select('general')
    cy.get('select[name="contentType"]').select('article')
    
    // Submit the form
    cy.get('button[type="submit"]').click()
    
    // Should redirect to styles list or show success message
    cy.get('[data-testid="success-message"]').should('contain', 'Style profile created')
  })

  it('should upload reference article', () => {
    cy.get('[data-testid="style-item"]').first().click()
    cy.url().should('include', '/dashboard/styles/')
    
    // Click upload button
    cy.get('[data-testid="upload-reference-button"]').click()
    
    // Upload file
    cy.get('input[type="file"]').selectFile('cypress/fixtures/sample-article.txt')
    cy.get('button[type="submit"]').click()
    
    // Should show success message
    cy.get('[data-testid="success-message"]').should('contain', 'Reference article uploaded')
  })

  it('should analyze style from reference articles', () => {
    cy.get('[data-testid="style-item"]').first().click()
    cy.url().should('include', '/dashboard/styles/')
    
    // Click analyze button
    cy.get('[data-testid="analyze-style-button"]').click()
    
    // Should show analysis results
    cy.get('[data-testid="style-analysis"]').should('be.visible')
    cy.get('[data-testid="tone-result"]').should('be.visible')
    cy.get('[data-testid="voice-result"]').should('be.visible')
    cy.get('[data-testid="target-audience-result"]').should('be.visible')
  })

  it('should edit style profile', () => {
    cy.get('[data-testid="style-item"]').first().click()
    cy.url().should('include', '/dashboard/styles/')
    
    // Click edit button
    cy.get('[data-testid="edit-style-button"]').click()
    
    // Update description
    cy.get('textarea[name="description"]').clear().type('Updated description')
    cy.get('button[type="submit"]').click()
    
    // Should show success message
    cy.get('[data-testid="success-message"]').should('contain', 'Style profile updated')
  })

  it('should delete style profile', () => {
    cy.get('[data-testid="style-item"]').first().click()
    cy.url().should('include', '/dashboard/styles/')
    
    // Click delete button
    cy.get('[data-testid="delete-style-button"]').click()
    
    // Confirm deletion in modal
    cy.get('[data-testid="confirm-delete-button"]').click()
    
    // Should redirect to styles list
    cy.url().should('include', '/dashboard/styles')
    cy.get('[data-testid="success-message"]').should('contain', 'Style profile deleted')
  })
})

describe('File Upload', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'password123')
  })

  it('should upload file successfully', () => {
    cy.visit('/dashboard/content/new')
    
    // Upload file
    cy.get('input[type="file"]').selectFile('cypress/fixtures/sample-document.pdf')
    
    // Should show file preview
    cy.get('[data-testid="file-preview"]').should('be.visible')
    cy.get('[data-testid="file-name"]').should('contain', 'sample-document.pdf')
  })

  it('should show error for invalid file type', () => {
    cy.visit('/dashboard/content/new')
    
    // Try to upload invalid file type
    cy.get('input[type="file"]').selectFile('cypress/fixtures/invalid-file.exe')
    
    // Should show error message
    cy.get('[data-testid="file-error"]').should('contain', 'Invalid file type')
  })

  it('should show error for file too large', () => {
    cy.visit('/dashboard/content/new')
    
    // Create a large file (this would need to be set up in fixtures)
    cy.get('input[type="file"]').selectFile('cypress/fixtures/large-file.txt')
    
    // Should show error message
    cy.get('[data-testid="file-error"]').should('contain', 'File too large')
  })

  it('should remove uploaded file', () => {
    cy.visit('/dashboard/content/new')
    
    // Upload file
    cy.get('input[type="file"]').selectFile('cypress/fixtures/sample-document.pdf')
    
    // Remove file
    cy.get('[data-testid="remove-file-button"]').click()
    
    // File preview should be gone
    cy.get('[data-testid="file-preview"]').should('not.exist')
  })
})

describe('Content Generation Workflow', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'password123')
  })

  it('should complete full content generation workflow', () => {
    // Step 1: Create style profile
    cy.visit('/dashboard/styles/new')
    cy.get('input[name="name"]').type('Test Workflow Style')
    cy.get('textarea[name="description"]').type('Style for testing workflow')
    cy.get('select[name="tone"]').select('professional')
    cy.get('select[name="voice"]').select('authoritative')
    cy.get('select[name="targetAudience"]').select('general')
    cy.get('select[name="contentType"]').select('article')
    cy.get('button[type="submit"]').click()
    
    // Should redirect to styles list
    cy.url().should('include', '/dashboard/styles')
    cy.get('[data-testid="success-message"]').should('contain', 'Style profile created')
    
    // Step 2: Upload reference article
    cy.get('[data-testid="style-item"]').contains('Test Workflow Style').click()
    cy.get('[data-testid="upload-reference-button"]').click()
    cy.get('input[type="file"]').selectFile('cypress/fixtures/sample-article.txt')
    cy.get('button[type="submit"]').click()
    
    // Step 3: Analyze style
    cy.get('[data-testid="analyze-style-button"]').click()
    cy.get('[data-testid="style-analysis"]').should('be.visible')
    
    // Step 4: Generate content
    cy.visit('/dashboard/content/new')
    cy.get('input[name="title"]').type('Workflow Test Article')
    cy.get('textarea[name="brief"]').type('This is a test brief for the workflow')
    cy.get('input[name="targetWords"]').type('1000')
    cy.get('select[name="styleProfile"]').select('Test Workflow Style')
    cy.get('button[type="submit"]').click()
    
    // Should show generation started message
    cy.get('[data-testid="success-message"]').should('contain', 'Content generation started')
    
    // Step 5: Check content status
    cy.visit('/dashboard/content')
    cy.get('[data-testid="content-item"]').contains('Workflow Test Article').should('be.visible')
  })
})
