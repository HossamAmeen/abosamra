import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import QtyStepper from './QtyStepper.vue'

describe('QtyStepper', () => {
  it('renders +, qty, - with Arabic aria-labels and 44px targets', () => {
    const w = mount(QtyStepper, { props: { modelValue: 2 } })
    expect(w.text()).toContain('2')
    expect(w.find('[data-test=inc]').attributes('aria-label')).toBe('زيادة الكمية')
    expect(w.find('[data-test=dec]').attributes('aria-label')).toBe('تقليل الكمية')
    expect(w.find('[data-test=inc]').classes()).toContain('h-11')
  })
  it('puts "+" first in DOM (start/right in RTL)', () => {
    const w = mount(QtyStepper, { props: { modelValue: 1 } })
    expect(w.findAll('button')[0].attributes('data-test')).toBe('inc')
  })
  it('emits +1 / -1', async () => {
    const w = mount(QtyStepper, { props: { modelValue: 2 } })
    await w.find('[data-test=inc]').trigger('click')
    await w.find('[data-test=dec]').trigger('click')
    expect(w.emitted('update:modelValue')).toEqual([[3], [1]])
  })
  it('respects min (product page min 1) and max', async () => {
    const w = mount(QtyStepper, { props: { modelValue: 1, min: 1, max: 3 } })
    expect(w.find('[data-test=dec]').attributes('disabled')).toBeDefined()
    await w.setProps({ modelValue: 3 })
    expect(w.find('[data-test=inc]').attributes('disabled')).toBeDefined()
    await w.find('[data-test=inc]').trigger('click')
    expect(w.emitted('update:modelValue')).toBeUndefined()
  })
  it('allows decrementing 1 -> 0 by default (removes the cart line)', async () => {
    const w = mount(QtyStepper, { props: { modelValue: 1 } })
    await w.find('[data-test=dec]').trigger('click')
    expect(w.emitted('update:modelValue')).toEqual([[0]])
  })
})
