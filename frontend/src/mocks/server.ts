/**
 * MSW server setup for Node.js environment (Jest tests)
 */

import { setupServer } from 'msw/node'
import { handlers } from './handlers'

// This configures a request mocking server with the given request handlers.
export const server = setupServer(...handlers)
