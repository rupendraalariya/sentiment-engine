import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'
import type { ApiStatus, PredictionHistoryItem, SentimentResult } from '@/types'
import { v4 as uuidv4 } from 'uuid'

// ---- simple uuid shim (no extra dep) ----
function uid() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36)
}

interface AppContextValue {
  history: PredictionHistoryItem[]
  addToHistory: (text: string, result: SentimentResult) => void
  clearHistory: () => void
  theme: 'dark' | 'light'
  toggleTheme: () => void
  apiStatus: ApiStatus
  setApiStatus: (s: ApiStatus) => void
}

const AppContext = createContext<AppContextValue | null>(null)

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [history, setHistory] = useState<PredictionHistoryItem[]>([])
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')
  const [apiStatus, setApiStatus] = useState<ApiStatus>('checking')

  // Persist theme
  useEffect(() => {
    const root = document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }, [theme])

  const addToHistory = useCallback((text: string, result: SentimentResult) => {
    setHistory((prev) => {
      const item: PredictionHistoryItem = {
        id: uid(),
        text,
        result,
        timestamp: new Date(),
      }
      return [item, ...prev].slice(0, 100)
    })
  }, [])

  const clearHistory = useCallback(() => setHistory([]), [])
  const toggleTheme = useCallback(
    () => setTheme((t) => (t === 'dark' ? 'light' : 'dark')),
    [],
  )

  return (
    <AppContext.Provider
      value={{ history, addToHistory, clearHistory, theme, toggleTheme, apiStatus, setApiStatus }}
    >
      {children}
    </AppContext.Provider>
  )
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used inside AppProvider')
  return ctx
}
