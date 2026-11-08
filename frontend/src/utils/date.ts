// Manual Arabic date helpers so digits stay Western (dayjs `ar` post-formats to Arabic-Indic).
const WEEKDAYS = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت']
const MONTHS = [
  'يناير',
  'فبراير',
  'مارس',
  'أبريل',
  'مايو',
  'يونيو',
  'يوليو',
  'أغسطس',
  'سبتمبر',
  'أكتوبر',
  'نوفمبر',
  'ديسمبر',
]

export const weekdayName = (iso: string | Date) => WEEKDAYS[new Date(iso).getDay()]

/** `12 نوفمبر` */
export function formatDayMonth(iso: string | Date): string {
  const d = new Date(iso)
  return `${d.getDate()} ${MONTHS[d.getMonth()]}`
}

/** `الخميس 12 نوفمبر` */
export const formatWeekdayDate = (iso: string | Date) =>
  `${weekdayName(iso)} ${formatDayMonth(iso)}`

/** `من 5 دقايق` style relative time. */
export function timeAgo(iso: string | Date, now = new Date()): string {
  const mins = Math.max(0, Math.floor((now.getTime() - new Date(iso).getTime()) / 60000))
  if (mins < 1) return 'دلوقتي'
  if (mins < 60) return `من ${mins} دقيقة`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `من ${hours} ساعة`
  return `من ${Math.floor(hours / 24)} يوم`
}

/** `النهاردة` / `امبارح` / `12 نوفمبر` for the customers list. */
export function dayLabel(iso: string | Date, now = new Date()): string {
  const d = new Date(iso)
  const days = Math.round(
    (new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime() -
      new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()) /
      86400000,
  )
  if (days <= 0) return 'النهاردة'
  if (days === 1) return 'امبارح'
  return formatDayMonth(d)
}
