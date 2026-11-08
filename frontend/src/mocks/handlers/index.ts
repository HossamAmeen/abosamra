import { adminHandlers } from './admin'
import { authHandlers } from './auth'
import { orderHandlers } from './orders'
import { publicHandlers } from './public'

export const handlers = [...publicHandlers, ...authHandlers, ...orderHandlers, ...adminHandlers]
