import { useCallback, useEffect, useState } from 'react'
import { getHealth } from '@/services/api'
import type { HealthResponse } from '@/types'
import { useApp } from '@/contexts/AppContext'

export function useApiStatus() {
  const { setApiStatus } = useApp()
  const [data, setData] = useState<HealthResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const check = useCallback(async () => {
    try {
      const res = await getHealth()
      setData(res)
      setApiStatus(res.status === 'ok' ? 'online' : 'offline')
    } catch {
      setData(null)
      setApiStatus('offline')
    } finally {
      setIsLoading(false)
    }
  }, [setApiStatus])

  useEffect(() => {
    check()
    const id = setInterval(check, 30_000)
    return () => clearInterval(id)
  }, [check])

  return { data, isLoading }
}
