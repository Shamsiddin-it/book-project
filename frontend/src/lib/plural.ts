/**
 * Русские окончания для чисел.
 *
 * Intl.PluralRules знает правило, но не знает самих форм — их всё равно нужно
 * передать. Зато он избавляет от ручной возни с «11-14 — особый случай»,
 * из-за которой обычно и появляется «1 подписчиков».
 */
const RULES = new Intl.PluralRules('ru-RU')

export function plural(count: number, one: string, few: string, many: string) {
  switch (RULES.select(count)) {
    case 'one':
      return one
    case 'few':
      return few
    default:
      return many
  }
}

export function withCount(count: number, one: string, few: string, many: string) {
  return `${count} ${plural(count, one, few, many)}`
}
