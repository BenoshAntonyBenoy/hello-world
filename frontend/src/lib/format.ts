export const pct = (n: number): string => `${Math.round(n)}%`

export const count = (n: number): string => n.toLocaleString('en-IN')

export function monthLabel(period: string): string {
  // period is YYYY-MM
  const [year, month] = period.split('-').map(Number)
  if (!year || !month) return period
  const date = new Date(year, month - 1, 1)
  return date.toLocaleDateString('en-GB', { month: 'short', year: '2-digit' })
}

export function dateLabel(iso: string | null): string {
  if (!iso) return 'Unknown'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function relativeDate(iso: string | null): string {
  if (!iso) return 'Unknown'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  const days = Math.round((Date.now() - date.getTime()) / 86_400_000)
  if (days <= 0) return 'Today'
  if (days === 1) return 'Yesterday'
  if (days < 30) return `${days} days ago`
  const months = Math.round(days / 30)
  return months === 1 ? '1 month ago' : `${months} months ago`
}

export function salaryLabel(job: {
  salary_min: number | null
  salary_max: number | null
  salary_currency: string | null
}): string | null {
  if (job.salary_min == null || job.salary_max == null) return null
  const lakh = (v: number) => (v / 100_000).toFixed(0)
  const symbol = job.salary_currency === 'INR' ? '₹' : ''
  return `${symbol}${lakh(job.salary_min)}–${lakh(job.salary_max)} LPA`
}

export function experienceLabel(min: number | null, max: number | null): string {
  if (min == null && max == null) return 'Not specified'
  if (min != null && max != null) return `${min}–${max} years`
  if (min != null) return `${min}+ years`
  return `Up to ${max} years`
}
