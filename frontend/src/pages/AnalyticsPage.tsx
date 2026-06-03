import Card from '@/components/ui/Card';
import { useMetrics } from '@/hooks/useMetrics';
import { BarChart3 } from 'lucide-react';

export default function AnalyticsPage() {
  const { data: metrics } = useMetrics();

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-2">Analytics</h1>
        <p className="text-muted-foreground">Performance insights and statistics</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card hover gradient>
          <div className="text-sm text-muted-foreground mb-1">Total Predictions</div>
          <div className="text-3xl font-bold text-primary">{metrics?.total_predictions || 0}</div>
        </Card>
        <Card hover gradient>
          <div className="text-sm text-muted-foreground mb-1">Avg Confidence</div>
          <div className="text-3xl font-bold text-green-400">N/A</div>
        </Card>
        <Card hover gradient>
          <div className="text-sm text-muted-foreground mb-1">Avg Latency</div>
          <div className="text-3xl font-bold text-blue-400">
            {metrics?.avg_latency_ms?.toFixed(2) || 0} ms
          </div>
        </Card>
        <Card hover gradient>
          <div className="text-sm text-muted-foreground mb-1">Throughput</div>
          <div className="text-3xl font-bold text-purple-400">
            {metrics?.predictions_per_second?.toFixed(2) || 0}/s
          </div>
        </Card>
      </div>

      {/* Charts Placeholder */}
      <Card gradient>
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-primary" />
          Performance Metrics
        </h2>
        <div className="h-64 flex items-center justify-center text-muted-foreground">
          <div className="text-center space-y-2">
            <BarChart3 className="w-16 h-16 mx-auto opacity-50" />
            <p>Charts will appear as you make predictions</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
