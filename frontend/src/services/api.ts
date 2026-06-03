import axios, { type AxiosError, type AxiosInstance } from 'axios'
import type {
  SentimentResult,
  BatchPredictResponse,
  HealthResponse,
  MetricsResponse,
} from '@/types'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

function createClient(): AxiosInstance {
  const client = axios.create({
    baseURL: BASE_URL,
    timeout: 10_000,
    headers: { 'Content-Type': 'application/json' },
  })

  // Request interceptor — log outgoing
  client.interceptors.request.use(
    (config) => {
      if (import.meta.env.DEV) {
        console.debug(`[API] ${config.method?.toUpperCase()} ${config.url}`)
      }
      return config
    },
    (error) => Promise.reject(error),
  )

  // Response interceptor — retry on 429 / 5xx
  client.interceptors.response.use(
    (res) => res,
    async (error: AxiosError) => {
      const config = error.config as typeof error.config & { _retry?: number }
      if (!config) return Promise.reject(error)
      config._retry = (config._retry ?? 0) + 1
      const status = error.response?.status ?? 0
      if (config._retry <= 3 && (status === 429 || status >= 500)) {
        await sleep(config._retry * 300)
        return client(config)
      }
      const msg =
        (error.response?.data as { detail?: string })?.detail ??
        error.message ??
        'Unknown API error'
      return Promise.reject(new Error(msg))
    },
  )

  return client
}

export const apiClient = createClient()

export async function predictSentiment(text: string): Promise<SentimentResult> {
  const { data } = await apiClient.post<SentimentResult>('/predict', { text })
  return data
}

export async function predictBatch(texts: string[]): Promise<BatchPredictResponse> {
  const { data } = await apiClient.post<BatchPredictResponse>('/predict/batch', { texts })
  return data
}

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/health')
  return data
}

export async function getMetrics(): Promise<MetricsResponse> {
  const { data } = await apiClient.get<MetricsResponse>('/metrics')
  return data
}
