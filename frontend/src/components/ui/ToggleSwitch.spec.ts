import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ToggleSwitch from './ToggleSwitch.vue'

describe('ToggleSwitch', () => {
  it('has role=switch and aria-checked reflecting state', async () => {
    const w = mount(ToggleSwitch, { props: { modelValue: false } })
    const btn = w.find('button')
    expect(btn.attributes('role')).toBe('switch')
    expect(btn.attributes('aria-checked')).toBe('false')
    await w.setProps({ modelValue: true })
    expect(btn.attributes('aria-checked')).toBe('true')
  })
  it('shows green label when ON and muted when OFF', async () => {
    const w = mount(ToggleSwitch, { props: { modelValue: true } })
    expect(w.text()).toBe('متوفر')
    expect(w.find('span span').exists()).toBe(true)
    expect(w.html()).toContain('text-success')
    await w.setProps({ modelValue: false })
    expect(w.text()).toBe('خلصان')
    expect(w.html()).toContain('text-muted')
  })
  it('emits the toggled value on click and Space', async () => {
    const w = mount(ToggleSwitch, { props: { modelValue: false } })
    await w.find('button').trigger('click')
    expect(w.emitted('update:modelValue')).toEqual([[true]])
  })
  it('does not emit when disabled; custom labels work', async () => {
    const w = mount(ToggleSwitch, {
      props: { modelValue: true, disabled: true, labelOn: 'شغّال', labelOff: 'واقف' },
    })
    expect(w.text()).toBe('شغّال')
    await w.find('button').trigger('click')
    expect(w.emitted('update:modelValue')).toBeUndefined()
  })
})
