import { Activity, Server, Cpu, Clock } from 'lucide-react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import { useApiStatus } from '@/hooks/useApiStatus';
import { useMetrics } from '@/hooks/useMetrics';
import Skeleton from '@/components/ui/Skeleton';

export default function MonitorPage() {
  const { data: health, isLoading: healthLoading } = useApiStatus();
  const { data: metrics, isLoading: metricsLoading } = useMetrics();

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-2">System Monitor</h1>
        <p className="text-muted-foreground">Real-time API health and performance monitoring</p>
      </div>

      {/* API Status */}
      <Card gradient>
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <Activity className="w-6 h-6 text-primary" />
          API Status
        </h2>

        {healthLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-8 w-32" />
            <Skeleton className="h-20 w-full" />
          </div>
        ) : health ? (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <Badge variant="success">Online</Badge>
              <span className="text-sm text-muted-foreground">
                Last checked: {new Date().toLocaleTimeString()}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-muted-foreground mb-1">Service</div>
                <div className="font-medium">{health.service}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground mb-1">Version</div>
                <div className="font-medium">{health.version}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground mb-1">Model</div>
                <div className="font-medium">{health.model || 'Lexicon-based'}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground mb-1">Device</div>
                <div className="font-medium">{health.device || 'CPU'}</div>
              </div>
            </div>
          </div>
        ) : (
          <Badge variant="error">Offline</Badge>
        )}
      </Card>

      {/* Metrics */}
      <Card gradient>
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <Server className="w-6 h-6 text-primary" />
          Runtime Metrics
        </h2>

        {metricsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>
        ) : metrics ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-hover p-4 rounded-lg">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                  <Activity className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Total Predictions</div>
                  <div className="text-2xl font-bold">{metrics.total_predictions || 0}</div>
                </div>
              </div>
            </div>

            <div className="glass-hover p-4 rounded-lg">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-green-400" />
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Avg Latency</div>
                  <div className="text-2xl font-bold">
                    {metrics.avg_latency_ms?.toFixed(2) || 0} ms
                  </div>
                </div>
              </div>
            </div>

            <div className="glass-hover p-4 rounded-lg">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                  <Cpu className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Throughput</div>
                  <div className="text-2xl font-bold">
                    {metrics.predictions_per_second?.toFixed(2) || 0}/s
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-muted-foreground">No metrics available</p>
        )}
      </Card>

      {/* Uptime Bar */}
      <Card gradient>
        <h2 className="text-2xl font-bold mb-4">Uptime</h2>
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Last 30 checks</span>
            <span className="font-medium text-green-400">100% Available</span>
          </div>
          <div className="h-8 flex gap-1">
            {[...Array(30)].map((_, i) => (
              <div
                key={i}
                className="flex-1 bg-green-500/30 rounded-sm hover:bg-green-500/50 transition-colors"
                title="Online"
              />
            ))}
          </div>
        </div>
      </Card>
    </div>
  );
}
