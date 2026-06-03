import { motion } from 'framer-motion';
import { Activity, TrendingUp, Zap, Clock } from 'lucide-react';
import Card from '@/components/ui/Card';
import { useMetrics } from '@/hooks/useMetrics';
import Skeleton from '@/components/ui/Skeleton';
import { formatNumber, formatLatency } from '@/utils/formatters';

export default function DashboardOverview() {
  const { data: metrics, isLoading } = useMetrics();

  const metricCards = [
    {
      title: 'Total Predictions',
      value: metrics?.total_predictions || 0,
      icon: Activity,
      color: 'from-blue-500 to-cyan-500',
      format: formatNumber,
    },
    {
      title: 'Avg Latency',
      value: metrics?.avg_latency_ms || 0,
      icon: Clock,
      color: 'from-green-500 to-emerald-500',
      format: formatLatency,
    },
    {
      title: 'Predictions/sec',
      value: metrics?.predictions_per_second || 0,
      icon: Zap,
      color: 'from-purple-500 to-pink-500',
      format: (v: number) => v.toFixed(2),
    },
    {
      title: 'Uptime',
      value: 99.9,
      icon: TrendingUp,
      color: 'from-orange-500 to-red-500',
      format: (v: number) => `${v}%`,
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold mb-2">Dashboard Overview</h1>
        <p className="text-muted-foreground">Monitor your sentiment analysis engine performance</p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metricCards.map((metric, index) => (
          <Card key={metric.title} hover gradient>
            {isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-10 w-10 rounded-lg" />
                <Skeleton className="h-8 w-24" />
                <Skeleton className="h-4 w-32" />
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${metric.color} flex items-center justify-center mb-4`}>
                  <metric.icon className="w-6 h-6 text-white" />
                </div>
                <div className={`text-3xl font-bold bg-gradient-to-r ${metric.color} bg-clip-text text-transparent mb-2`}>
                  {metric.format(metric.value)}
                </div>
                <div className="text-sm text-muted-foreground">{metric.title}</div>
              </motion.div>
            )}
          </Card>
        ))}
      </div>

      {/* Quick Predict */}
      <Card gradient>
        <h2 className="text-2xl font-bold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <motion.a
            href="/dashboard/predict"
            whileHover={{ scale: 1.02 }}
            className="glass-hover p-6 rounded-lg text-center space-y-2 block"
          >
            <div className="text-4xl mb-2">🎯</div>
            <div className="font-semibold">Single Prediction</div>
            <div className="text-sm text-muted-foreground">Analyze one text</div>
          </motion.a>

          <motion.a
            href="/dashboard/batch"
            whileHover={{ scale: 1.02 }}
            className="glass-hover p-6 rounded-lg text-center space-y-2 block"
          >
            <div className="text-4xl mb-2">📦</div>
            <div className="font-semibold">Batch Processing</div>
            <div className="text-sm text-muted-foreground">Analyze multiple texts</div>
          </motion.a>

          <motion.a
            href="/dashboard/analytics"
            whileHover={{ scale: 1.02 }}
            className="glass-hover p-6 rounded-lg text-center space-y-2 block"
          >
            <div className="text-4xl mb-2">📊</div>
            <div className="font-semibold">View Analytics</div>
            <div className="text-sm text-muted-foreground">Performance insights</div>
          </motion.a>
        </div>
      </Card>

      {/* System Info */}
      <Card gradient>
        <h2 className="text-2xl font-bold mb-4">System Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="text-sm text-muted-foreground mb-1">Model</div>
            <div className="font-medium">{metrics?.model_name || 'Lexicon-based'}</div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground mb-1">Device</div>
            <div className="font-medium">{metrics?.device || 'CPU'}</div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground mb-1">Service</div>
            <div className="font-medium">Sentiment Analysis Engine v0.1.0</div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground mb-1">Status</div>
            <div className="font-medium text-green-400">Operational</div>
          </div>
        </div>
      </Card>
    </div>
  );
}
