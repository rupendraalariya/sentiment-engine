import type { SentimentLabel } from '@/types'

export function formatConfidence(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

export function formatLatency(ms: number): string {
  if (ms < 1) return `${(ms * 1000).toFixed(0)}µs`
  if (ms < 1000) return `${ms.toFixed(1)}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

export function formatUptime(seconds: number): string {
  if (seconds < 60) return `${Math.floor(seconds)}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s`
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${h}h ${m}m`
}

export function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return n.toString()
}

export function getSentimentColor(label: SentimentLabel): string {
  switch (label) {
    case 'positive': return '#22C55E'
    case 'negative': return '#EF4444'
    case 'neutral':  return '#F59E0B'
  }
}

export function getSentimentBg(label: SentimentLabel): string {
  switch (label) {
    case 'positive': return 'bg-positive/20 text-positive border-positive/30'
    case 'negative': return 'bg-negative/20 text-negative border-negative/30'
    case 'neutral':  return 'bg-neutral-sentiment/20 text-neutral-sentiment border-neutral-sentiment/30'
  }
}

export function getSentimentEmoji(label: SentimentLabel): string {
  switch (label) {
    case 'positive': return '😊'
    case 'negative': return '😞'
    case 'neutral':  return '😐'
  }
}

export function getSentimentGlow(label: SentimentLabel): string {
  switch (label) {
    case 'positive': return 'shadow-glow-positive'
    case 'negative': return 'shadow-glow-negative'
    case 'neutral':  return 'shadow-[0_0_20px_rgba(245,158,11,0.3)]'
  }
}

export function truncateText(text: string, maxLength: number = 60): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '…'
}
