export function highlight(text: string, query: string): string {
  if (!query.trim()) return text
  const q = query.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const re = new RegExp(`(${q})`, 'ig')
  return text.replace(re, '<mark>$1</mark>')
}
