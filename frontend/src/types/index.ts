export type SentimentLabel = 'positive' | 'negative' | 'neutral'

export interface SentimentResult {
  label: SentimentLabel
  confidence: number
  scores: { negative: number; neutral: number; positive: number }
  processing_time_ms: number
}

export interface BatchPredictResponse {
  results: SentimentResult[]
  total_time_ms: number
}

export interface HealthResponse {
  status: string
  model: string
  device: string
}

export interface MetricsResponse {
  total_predictions: number
  average_latency_ms: number
  predictions_per_second: number
  uptime_seconds: number
}

export interface PredictionHistoryItem {
  id: string
  text: string
  result: SentimentResult
  timestamp: Date
}

export type ApiStatus = 'online' | 'offline' | 'checking'

export interface ChartDataPoint {
  name: string
  value: number
  color?: string
}
