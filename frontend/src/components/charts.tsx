import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { DistributionBucket, Trend } from '@/lib/types'
import { count, monthLabel, pct } from '@/lib/format'
import { cx } from './ui'

const AXIS = 'rgb(var(--faint))'
const GRID = 'rgb(var(--line))'

/** Shared tooltip so every chart reads the same way. */
function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: { name?: string; value?: number | string; color?: string; payload?: unknown }[]
  label?: string | number
}) {
  if (!active || !payload?.length) return null
  const point = payload[0]?.payload as { total_jobs?: number } | undefined
  return (
    <div className="rounded-lg border border-line bg-surface px-3 py-2 shadow-lift">
      <p className="text-xs font-medium">{monthLabel(String(label))}</p>
      {payload.map((entry) => (
        <p key={entry.name} className="tnum mt-0.5 text-xs text-muted">
          <span
            className="mr-1.5 inline-block h-2 w-2 rounded-full align-middle"
            style={{ background: entry.color }}
          />
          {entry.name}: <span className="font-semibold text-ink">{pct(Number(entry.value))}</span>
        </p>
      ))}
      {point?.total_jobs != null && (
        <p className="tnum mt-1 border-t border-line pt-1 text-2xs text-faint">
          {count(point.total_jobs)} postings that month
        </p>
      )}
    </div>
  )
}

const SERIES_COLORS = [
  'rgb(var(--brand))',
  '#0ea5e9',
  '#10b981',
  '#f59e0b',
  '#ec4899',
  '#8b5cf6',
]

/**
 * Multi-series monthly frequency. Series are aligned on period so a skill that
 * only appears in later months still lines up correctly on the x-axis.
 */
export function TrendChart({ trends, height = 300 }: { trends: Trend[]; height?: number }) {
  if (!trends.length) return null

  const periods = Array.from(
    new Set(trends.flatMap((t) => t.points.map((p) => p.period))),
  ).sort()

  const data = periods.map((period) => {
    const row: Record<string, string | number | null> = { period }
    let total: number | null = null
    for (const trend of trends) {
      const point = trend.points.find((p) => p.period === period)
      row[trend.skill.canonical] = point ? point.frequency_pct : null
      if (point && total == null) total = point.total_jobs
    }
    row.total_jobs = total
    return row
  })

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: -18 }}>
          <CartesianGrid stroke={GRID} strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="period"
            tickFormatter={monthLabel}
            tick={{ fill: AXIS, fontSize: 11 }}
            tickLine={false}
            axisLine={{ stroke: GRID }}
            minTickGap={12}
          />
          <YAxis
            tick={{ fill: AXIS, fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => `${v}%`}
            width={48}
          />
          <Tooltip content={<ChartTooltip />} cursor={{ stroke: GRID }} />
          <Legend
            verticalAlign="bottom"
            height={34}
            iconType="plainline"
            iconSize={14}
            formatter={(value) => (
              <span className="text-xs text-muted">{String(value)}</span>
            )}
          />
          {trends.map((trend, i) => (
            <Line
              key={trend.skill.slug}
              type="monotone"
              dataKey={trend.skill.canonical}
              stroke={SERIES_COLORS[i % SERIES_COLORS.length]}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Compact inline sparkline for a single skill's history. */
export function Sparkline({ trend }: { trend: Trend }) {
  const values = trend.points.map((p) => p.frequency_pct)
  if (values.length < 2) return null

  const max = Math.max(...values, 1)
  const min = Math.min(...values, 0)
  const span = max - min || 1
  const width = 92
  const height = 26

  const points = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * width
      const y = height - ((v - min) / span) * height
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')

  const tone =
    trend.direction === 'emerging'
      ? 'rgb(var(--low))'
      : trend.direction === 'declining'
        ? 'rgb(var(--high))'
        : 'rgb(var(--faint))'

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="h-6 w-24 shrink-0 overflow-visible"
      aria-hidden
    >
      <polyline
        points={points}
        fill="none"
        stroke={tone}
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

/** Horizontal distribution bars — used for experience and education splits. */
export function DistributionBars({
  buckets,
  emptyLabel = 'No data',
}: {
  buckets: DistributionBucket[]
  emptyLabel?: string
}) {
  const shown = buckets.filter((b) => b.count > 0)
  if (!shown.length) return <p className="text-sm text-muted">{emptyLabel}</p>

  return (
    <ul className="space-y-2.5">
      {shown.map((bucket, i) => (
        <li key={bucket.label} className="grid grid-cols-[7.5rem_1fr_3rem] items-center gap-3">
          <span className="truncate text-sm text-muted" title={bucket.label}>
            {bucket.label}
          </span>
          <span className="h-2 overflow-hidden rounded-full bg-raised">
            <span
              className="block h-full origin-left animate-grow rounded-full bg-brand/70"
              style={{ width: `${bucket.pct}%`, animationDelay: `${i * 40}ms` }}
            />
          </span>
          <span className="tnum text-right text-sm font-medium">{pct(bucket.pct)}</span>
        </li>
      ))}
    </ul>
  )
}

/** Readiness ring for the skill-gap page. */
export function ReadinessRing({ value, size = 132 }: { value: number; size?: number }) {
  const stroke = 10
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const clamped = Math.max(0, Math.min(100, value))
  const offset = circumference * (1 - clamped / 100)

  const tone =
    clamped >= 70 ? 'rgb(var(--low))' : clamped >= 40 ? 'rgb(var(--medium))' : 'rgb(var(--brand))'

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgb(var(--line))"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={tone}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 900ms cubic-bezier(0.16,1,0.3,1)' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="tnum text-3xl font-semibold tracking-tight">{Math.round(clamped)}%</span>
        <span className="text-2xs uppercase tracking-wider text-faint">ready</span>
      </div>
    </div>
  )
}

export function DirectionChip({ direction }: { direction: Trend['direction'] }) {
  const map = {
    emerging: { label: 'Rising', tone: 'border-low/30 bg-low/10 text-low', arrow: 'M7 17 17 7M17 7H9m8 0v8' },
    declining: { label: 'Falling', tone: 'border-high/30 bg-high/10 text-high', arrow: 'M7 7l10 10M17 17H9m8 0V9' },
    stable: { label: 'Stable', tone: 'border-line bg-raised text-muted', arrow: 'M5 12h14' },
    insufficient_data: { label: 'Not enough data', tone: 'border-line bg-raised text-faint', arrow: 'M5 12h14' },
  }[direction]

  return (
    <span className={cx('chip', map.tone)}>
      <svg viewBox="0 0 24 24" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d={map.arrow} />
      </svg>
      {map.label}
    </span>
  )
}
