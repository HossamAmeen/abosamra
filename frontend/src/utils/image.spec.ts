import { describe, expect, it } from 'vitest'
import { fitWithin } from './image'

describe('fitWithin', () => {
  it('scales the longest side down to 1200', () => {
    expect(fitWithin(4000, 3000)).toEqual({ width: 1200, height: 900 })
    expect(fitWithin(1000, 3000)).toEqual({ width: 400, height: 1200 })
  })
  it('never upscales', () => {
    expect(fitWithin(800, 600)).toEqual({ width: 800, height: 600 })
  })
})
