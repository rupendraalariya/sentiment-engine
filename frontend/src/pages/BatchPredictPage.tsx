import { useState } from 'react';
import { motion } from 'framer-motion';
import { Upload, Download, Layers } from 'lucide-react';
import toast from 'react-hot-toast';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import { predictBatch } from '@/services/api';
import type { SentimentResult } from '@/types';

export default function BatchPredictPage() {
  const [texts, setTexts] = useState('');
  const [results, setResults] = useState<SentimentResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleBatchPredict = async () => {
    const textArray = texts
      .split('\n')
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    if (textArray.length === 0) {
      toast.error('Please enter at least one text');
      return;
    }

    if (textArray.length > 64) {
      toast.error('Maximum 64 texts allowed per batch');
      return;
    }

    setIsLoading(true);
    try {
      const response = await predictBatch(textArray);
      setResults(response.results);
      toast.success(`Processed ${response.results.length} predictions!`);
    } catch (error) {
      toast.error('Failed to process batch');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportCSV = () => {
    if (results.length === 0) return;

    const csv = [
      ['Text', 'Sentiment', 'Confidence', 'Positive', 'Negative', 'Neutral'],
      ...results.map((r) => [
        r.text || '',
        r.label,
        (r.confidence * 100).toFixed(2),
        ((r.scores?.positive || 0) * 100).toFixed(2),
        ((r.scores?.negative || 0) * 100).toFixed(2),
        ((r.scores?.neutral || 0) * 100).toFixed(2),
      ]),
    ]
      .map((row) => row.map((cell) => `"${cell}"`).join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sentiment-results-${Date.now()}.csv`;
    a.click();
    toast.success('CSV exported!');
  };

  const handleExportJSON = () => {
    if (results.length === 0) return;

    const json = JSON.stringify(results, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sentiment-results-${Date.now()}.json`;
    a.click();
    toast.success('JSON exported!');
  };

  const getSentimentColor = (sentiment: string | undefined) => {
    if (!sentiment) return 'neutral';
    switch (sentiment.toLowerCase()) {
      case 'positive':
        return 'positive';
      case 'negative':
        return 'negative';
      default:
        return 'neutral';
    }
  };

  const summary = results.length > 0 && {
    total: results.length,
    positive: results.filter((r) => r.label.toLowerCase() === 'positive').length,
    negative: results.filter((r) => r.label.toLowerCase() === 'negative').length,
    neutral: results.filter((r) => r.label.toLowerCase() === 'neutral').length,
    avgConfidence: (results.reduce((sum, r) => sum + r.confidence, 0) / results.length) * 100,
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-2">Batch Prediction</h1>
        <p className="text-muted-foreground">Process up to 64 texts simultaneously</p>
      </div>

      {/* Input Section */}
      <Card gradient>
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <Layers className="w-6 h-6 text-primary" />
          Enter Multiple Texts
        </h2>

        <textarea
          value={texts}
          onChange={(e) => setTexts(e.target.value)}
          placeholder="Enter one text per line..."
          className="w-full h-48 px-4 py-3 rounded-lg glass border border-white/10 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none font-mono text-sm"
        />

        <div className="flex items-center justify-between mt-4">
          <div className="text-sm text-muted-foreground">
            {texts.split('\n').filter((t) => t.trim()).length} texts • Max 64 per batch
          </div>
          <Button variant="primary" onClick={handleBatchPredict} isLoading={isLoading}>
            <Upload className="w-4 h-4 mr-2" />
            Process Batch
          </Button>
        </div>
      </Card>

      {/* Summary */}
      {summary && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <Card gradient>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold">Summary</h2>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={handleExportCSV}>
                  <Download className="w-4 h-4 mr-2" />
                  CSV
                </Button>
                <Button variant="outline" size="sm" onClick={handleExportJSON}>
                  <Download className="w-4 h-4 mr-2" />
                  JSON
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-primary">{summary.total}</div>
                <div className="text-sm text-muted-foreground">Total</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-400">{summary.positive}</div>
                <div className="text-sm text-muted-foreground">Positive</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-red-400">{summary.negative}</div>
                <div className="text-sm text-muted-foreground">Negative</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-400">{summary.neutral}</div>
                <div className="text-sm text-muted-foreground">Neutral</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-primary">{summary.avgConfidence.toFixed(1)}%</div>
                <div className="text-sm text-muted-foreground">Avg Confidence</div>
              </div>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Results Table */}
      {results.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <Card gradient>
            <h2 className="text-2xl font-bold mb-4">Results</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left py-3 px-4">#</th>
                    <th className="text-left py-3 px-4">Text</th>
                    <th className="text-left py-3 px-4">Sentiment</th>
                    <th className="text-left py-3 px-4">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((result, index) => (
                    <motion.tr
                      key={index}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: index * 0.05 }}
                      className="border-b border-white/5 hover:bg-white/5"
                    >
                      <td className="py-3 px-4 text-muted-foreground">{index + 1}</td>
                      <td className="py-3 px-4 max-w-md truncate">{result.text}</td>
                      <td className="py-3 px-4">
                        <Badge variant={getSentimentColor(result.label)}>
                          {result.label}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 font-medium">
                        {(result.confidence * 100).toFixed(1)}%
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
