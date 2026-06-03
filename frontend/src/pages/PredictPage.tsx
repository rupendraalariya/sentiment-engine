import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import { predictSentiment } from '@/services/api';
import type { SentimentResult } from '@/types';

const exampleTexts = [
  'This product is absolutely amazing! I love it!',
  'Terrible experience, very disappointed.',
  'It works fine, nothing special.',
];

export default function PredictPage() {
  const [text, setText] = useState('');
  const [result, setResult] = useState<SentimentResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handlePredict = async () => {
    if (!text.trim()) {
      toast.error('Please enter some text');
      return;
    }

    setIsLoading(true);
    try {
      const response = await predictSentiment(text);
      setResult(response);
      toast.success('Prediction complete!');
    } catch (error) {
      toast.error('Failed to predict sentiment');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handlePredict();
    }
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

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-2">Sentiment Prediction</h1>
        <p className="text-muted-foreground">Analyze the sentiment of any text in real-time</p>
      </div>

      {/* Input Section */}
      <Card gradient>
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-primary" />
          Enter Your Text
        </h2>

        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="Type or paste your text here..."
          className="w-full h-40 px-4 py-3 rounded-lg glass border border-white/10 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
        />

        <div className="flex items-center justify-between mt-4">
          <div className="text-sm text-muted-foreground">
            {text.length} characters • Press Ctrl+Enter to predict
          </div>
          <Button
            variant="primary"
            onClick={handlePredict}
            isLoading={isLoading}
            disabled={!text.trim()}
          >
            <Send className="w-4 h-4 mr-2" />
            Predict Sentiment
          </Button>
        </div>

        {/* Example Chips */}
        <div className="mt-6 space-y-2">
          <div className="text-sm text-muted-foreground">Try examples:</div>
          <div className="flex flex-wrap gap-2">
            {exampleTexts.map((example, index) => (
              <motion.button
                key={index}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setText(example)}
                className="px-3 py-1 rounded-full glass-hover text-sm border border-white/10"
              >
                {example.slice(0, 40)}...
              </motion.button>
            ))}
          </div>
        </div>
      </Card>

      {/* Result Section */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <Card gradient className="space-y-6">
              <h2 className="text-2xl font-bold">Result</h2>

              {/* Main Sentiment Badge */}
              <div className="flex items-center justify-center">
                <Badge
                  variant={getSentimentColor(result?.label)}
                  className="text-2xl px-8 py-4"
                >
                  {result?.label?.toUpperCase() || 'UNKNOWN'}
                </Badge>
              </div>

              {/* Confidence Circle */}
              <div className="flex justify-center">
                <div className="relative w-32 h-32">
                  <svg className="transform -rotate-90 w-32 h-32">
                    <circle
                      cx="64"
                      cy="64"
                      r="56"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="none"
                      className="text-white/10"
                    />
                    <circle
                      cx="64"
                      cy="64"
                      r="56"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="none"
                      strokeDasharray={`${2 * Math.PI * 56}`}
                      strokeDashoffset={`${2 * Math.PI * 56 * (1 - result.confidence)}`}
                      className="text-primary"
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <div className="text-3xl font-bold">{(result.confidence * 100).toFixed(1)}%</div>
                      <div className="text-xs text-muted-foreground">Confidence</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Probabilities */}
              <div className="space-y-3">
                <h3 className="font-semibold text-lg">Probability Distribution</h3>
                {result.scores && (
                  <div className="space-y-2">
                    {Object.entries(result.scores).map(([label, prob]) => (
                      <div key={label}>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="capitalize">{label}</span>
                          <span className="font-medium">{(prob * 100).toFixed(2)}%</span>
                        </div>
                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${prob * 100}%` }}
                            transition={{ duration: 0.5, delay: 0.2 }}
                            className={`h-full ${
                              label === 'positive'
                                ? 'bg-green-500'
                                : label === 'negative'
                                ? 'bg-red-500'
                                : 'bg-gray-500'
                            }`}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Metadata */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/10">
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Inference Time</div>
                  <div className="font-medium">{result.processing_time_ms?.toFixed(2) || 'N/A'} ms</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Text Length</div>
                  <div className="font-medium">{text.length} chars</div>
                </div>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
