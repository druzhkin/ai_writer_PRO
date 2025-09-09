/**
 * MSW (Mock Service Worker) handlers for API mocking in tests
 */

import { http, HttpResponse } from 'msw'

// Mock data
const mockUser = {
  id: '1',
  email: 'test@example.com',
  username: 'testuser',
  first_name: 'Test',
  last_name: 'User',
  is_active: true,
  is_verified: true,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
}

const mockOrganization = {
  id: '1',
  name: 'Test Organization',
  slug: 'test-org',
  description: 'A test organization',
  subscription_plan: 'free',
  subscription_status: 'active',
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
}

const mockStyleProfile = {
  id: '1',
  name: 'Test Style',
  description: 'A test style profile',
  tone: 'professional',
  voice: 'authoritative',
  target_audience: 'general',
  content_type: 'article',
  organization_id: '1',
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
}

const mockGeneratedContent = {
  id: '1',
  title: 'Test Article',
  content: 'This is test generated content.',
  brief: 'Test brief for content generation',
  target_words: 1000,
  status: 'completed',
  user_id: '1',
  organization_id: '1',
  style_profile_id: '1',
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
}

const mockAccessToken = 'mock-access-token'

// Auth handlers
export const authHandlers = [
  // Login
  http.post('/api/v1/auth/login', async ({ request }) => {
    const body = await request.json() as { email: string; password: string }
    
    if (body.email === 'test@example.com' && body.password === 'password123') {
      return HttpResponse.json({
        access_token: mockAccessToken,
        token_type: 'bearer',
        user: mockUser,
      })
    }
    
    return HttpResponse.json(
      { detail: 'Invalid credentials' },
      { status: 401 }
    )
  }),

  // Register
  http.post('/api/v1/auth/register', async ({ request }) => {
    const body = await request.json() as any
    
    return HttpResponse.json({
      user: {
        ...mockUser,
        email: body.email,
        username: body.username,
        first_name: body.first_name,
        last_name: body.last_name,
      },
      access_token: mockAccessToken,
      token_type: 'bearer',
    }, { status: 201 })
  }),

  // Get current user
  http.get('/api/v1/users/me', ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    
    if (!authHeader || !authHeader.includes(mockAccessToken)) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    return HttpResponse.json(mockUser)
  }),

  // Update user
  http.put('/api/v1/users/me', async ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    const body = await request.json() as any
    
    if (!authHeader || !authHeader.includes(mockAccessToken)) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    return HttpResponse.json({
      ...mockUser,
      ...body,
    })
  }),

  // Password reset request
  http.post('/api/v1/auth/password-reset', async ({ request }) => {
    const body = await request.json() as { email: string }
    
    return HttpResponse.json({
      message: 'Password reset email sent',
    })
  }),

  // Password reset confirm
  http.post('/api/v1/auth/password-reset/confirm', async ({ request }) => {
    const body = await request.json() as { token: string; new_password: string }
    
    if (body.token === 'invalid_token') {
      return HttpResponse.json(
        { detail: 'Invalid or expired token' },
        { status: 400 }
      )
    }
    
    return HttpResponse.json({
      message: 'Password reset successfully',
    })
  }),
]

// Organization handlers
export const organizationHandlers = [
  // Get organizations
  http.get('/api/v1/organizations/', ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    
    if (!authHeader || !authHeader.includes(mockAccessToken)) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    return HttpResponse.json([mockOrganization])
  }),

  // Create organization
  http.post('/api/v1/organizations/', async ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    const body = await request.json() as any
    
    if (!authHeader || !authHeader.includes(mockAccessToken)) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    return HttpResponse.json({
      ...mockOrganization,
      name: body.name,
      description: body.description,
    }, { status: 201 })
  }),

  // Get organization details
  http.get('/api/v1/organizations/:id', ({ request, params }) => {
    const authHeader = request.headers.get('Authorization')
    
    if (!authHeader || !authHeader.includes(mockAccessToken)) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    return HttpResponse.json(mockOrganization)
  }),

  // Update organization
  http.put('/api/v1/organizations/:id', async ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    const body = await request.json() as any
    
    if (!authHeader || !authHeader.includes(mockAccessToken)) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    return HttpResponse.json({
      ...mockOrganization,
      ...body,
    })
  }),
]

// Style handlers
export const styleHandlers = [
  // Get style profiles
  http.get('/api/v1/styles/', ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    
    if (!authHeader || !authHeader.includes(mockAccessToken)) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    return HttpResponse.json([mockStyleProfile])
  }),

  // Create style profile
  http.post('/api/v1/styles/', async ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    const body = await request.json() as any
    
    if (!authHeader || !authHeader.includes(mockAccessToken)) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    return HttpResponse.json({
      ...mockStyleProfile,
      name: body.name,
      description: body.description,
      tone: body.tone,
      voice: body.voice,
      target_audience: body.target_audience,
      content_type: body.content_type,
    }, { status: 201 })
  }),

  // Upload reference article
  http.post('/api/v1/styles/upload-reference', async ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    
    if (!authHeader || !authHeader.includes(mockAccessToken)) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    return HttpResponse.json({
      article: {
        id: '1',
        title: 'Test Reference Article',
        content: 'Test content',
        url: 'https://example.com/test-article',
        author: 'Test Author',
        style_profile_id: '1',
        created_at: '2023-01-01T00:00:00Z',
      },
    }, { status: 201 })
  }),
]

// Content handlers
export const contentHandlers = [
  // Get generated content
  http.get('/api/v1/content/', ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    
    if (!authHeader || !authHeader.includes(mockAccessToken)) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    return HttpResponse.json([mockGeneratedContent])
  }),

  // Generate content
  http.post('/api/v1/content/generate', async ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    const body = await request.json() as any
    
    if (!authHeader || !authHeader.includes(mockAccessToken)) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    return HttpResponse.json({
      task_id: 'mock-task-id',
      message: 'Content generation started',
    }, { status: 202 })
  }),

  // Get content details
  http.get('/api/v1/content/:id', ({ request, params }) => {
    const authHeader = request.headers.get('Authorization')
    
    if (!authHeader || !authHeader.includes(mockAccessToken)) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    return HttpResponse.json(mockGeneratedContent)
  }),

  // Update content
  http.put('/api/v1/content/:id', async ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    const body = await request.json() as any
    
    if (!authHeader || !authHeader.includes(mockAccessToken)) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    return HttpResponse.json({
      ...mockGeneratedContent,
      ...body,
    })
  }),

  // Delete content
  http.delete('/api/v1/content/:id', ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    
    if (!authHeader || !authHeader.includes(mockAccessToken)) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    return new HttpResponse(null, { status: 204 })
  }),
]

// File handlers
export const fileHandlers = [
  // Upload file
  http.post('/api/v1/files/upload', async ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    
    if (!authHeader || !authHeader.includes(mockAccessToken)) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    return HttpResponse.json({
      file_url: 'https://example.com/uploaded-file.txt',
      filename: 'test.txt',
      size: 1024,
      content_type: 'text/plain',
    }, { status: 201 })
  }),
]

// Usage handlers
export const usageHandlers = [
  // Get usage stats
  http.get('/api/v1/usage/stats', ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    
    if (!authHeader || !authHeader.includes(mockAccessToken)) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    return HttpResponse.json({
      total_tokens: 1000,
      total_cost: 0.10,
      usage_by_date: [
        { date: '2023-01-01', tokens: 100, cost: 0.01 },
        { date: '2023-01-02', tokens: 200, cost: 0.02 },
      ],
    })
  }),

  // Get usage history
  http.get('/api/v1/usage/history', ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    
    if (!authHeader || !authHeader.includes(mockAccessToken)) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }
    
    return HttpResponse.json([
      {
        id: '1',
        endpoint: '/api/v1/content/generate',
        method: 'POST',
        tokens_used: 100,
        cost: 0.01,
        response_time: 1.5,
        created_at: '2023-01-01T00:00:00Z',
      },
    ])
  }),
]

// Health check handler
export const healthHandlers = [
  http.get('/health', () => {
    return HttpResponse.json({
      status: 'healthy',
      service: 'AI Writer PRO Backend',
      version: '0.1.0',
      environment: 'test',
    })
  }),
]

// OAuth handlers
export const oauthHandlers = [
  // Google OAuth authorize
  http.get('/api/v1/oauth/google/authorize', () => {
    return HttpResponse.redirect('https://accounts.google.com/oauth/authorize?client_id=mock&redirect_uri=mock&state=mock')
  }),

  // GitHub OAuth authorize
  http.get('/api/v1/oauth/github/authorize', () => {
    return HttpResponse.redirect('https://github.com/login/oauth/authorize?client_id=mock&redirect_uri=mock&state=mock')
  }),

  // OAuth callback
  http.get('/api/v1/oauth/callback', ({ request }) => {
    const url = new URL(request.url)
    const state = url.searchParams.get('state')
    
    if (state === 'invalid') {
      return HttpResponse.json(
        { detail: 'Invalid state parameter' },
        { status: 400 }
      )
    }
    
    return HttpResponse.json({
      access_token: mockAccessToken,
      token_type: 'bearer',
      user: mockUser,
    })
  }),
]

// Combine all handlers
export const handlers = [
  ...authHandlers,
  ...organizationHandlers,
  ...styleHandlers,
  ...contentHandlers,
  ...fileHandlers,
  ...usageHandlers,
  ...healthHandlers,
  ...oauthHandlers,
]
