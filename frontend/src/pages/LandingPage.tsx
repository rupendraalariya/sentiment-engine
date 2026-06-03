import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Zap,
  Layers,
  Cpu,
  Database,
  BarChart3,
  Shield,
  Github,
  ArrowRight,
  Sparkles,
  User,
  Mail,
  Linkedin,
} from 'lucide-react';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';

const features = [
  {
    icon: Zap,
    title: 'Real-Time Analysis',
    description: 'Lightning-fast sentiment detection with <100ms response time',
  },
  {
    icon: Layers,
    title: 'Batch Processing',
    description: 'Process up to 64 texts simultaneously with optimized throughput',
  },
  {
    icon: Cpu,
    title: 'ONNX Acceleration',
    description: 'Hardware-optimized inference with ONNX Runtime',
  },
  {
    icon: Database,
    title: 'REST API',
    description: 'Production-ready API with OpenAPI documentation',
  },
  {
    icon: BarChart3,
    title: 'Analytics Dashboard',
    description: 'Real-time metrics, charts, and performance monitoring',
  },
  {
    icon: Shield,
    title: 'Enterprise Ready',
    description: 'Docker deployment, health checks, and 99.9% uptime',
  },
];

const stats = [
  { label: 'Accuracy', value: '95%+', color: 'from-green-500 to-emerald-500' },
  { label: 'Latency', value: '<100ms', color: 'from-blue-500 to-cyan-500' },
  { label: 'Throughput', value: '1000+', color: 'from-purple-500 to-pink-500' },
  { label: 'Uptime', value: '99.9%', color: 'from-orange-500 to-red-500' },
];

const skills = [
  'Python',
  'FastAPI',
  'PyTorch',
  'Transformers',
  'TensorFlow',
  'Docker',
  'AWS',
  'React',
  'TypeScript',
  'MongoDB',
  'PostgreSQL',
  'Machine Learning',
  'Deep Learning',
  'LLMs',
  'RAG Systems',
  'Generative AI',
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-secondary/20 to-accent/20 opacity-30" />
        <div className="absolute inset-0">
          {[...Array(20)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-2 h-2 bg-primary rounded-full"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
              }}
              animate={{
                y: [0, -30, 0],
                opacity: [0.2, 0.8, 0.2],
              }}
              transition={{
                duration: 3 + Math.random() * 2,
                repeat: Infinity,
                delay: Math.random() * 2,
              }}
            />
          ))}
        </div>

        <div className="container mx-auto px-4 relative z-10">
          <div className="text-center space-y-8">
            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-center"
            >
              <Badge variant="default" className="gap-2">
                <Sparkles className="w-4 h-4" />
                Powered by BERT & ONNX Runtime
              </Badge>
            </motion.div>

            {/* Heading */}
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="text-5xl md:text-7xl font-bold"
            >
              <span className="bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
                AI Sentiment Analysis
              </span>
              <br />
              <span className="text-foreground">Engine</span>
            </motion.h1>

            {/* Subheading */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto"
            >
              Enterprise-grade sentiment intelligence powered by BERT, Transformers, and ONNX Runtime.
              Real-time analysis with 95%+ accuracy.
            </motion.p>

            {/* CTA Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="flex flex-wrap items-center justify-center gap-4"
            >
              <Link to="/dashboard">
                <Button variant="primary" size="lg" className="gap-2">
                  Try Demo <ArrowRight className="w-5 h-5" />
                </Button>
              </Link>
              <Link to="/dashboard">
                <Button variant="outline" size="lg">
                  View Dashboard
                </Button>
              </Link>
              <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">
                <Button variant="ghost" size="lg">
                  API Docs
                </Button>
              </a>
              <a
                href="https://github.com/rupendraalariya/sentiment-engine"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="ghost" size="lg" className="gap-2">
                  <Github className="w-5 h-5" /> GitHub
                </Button>
              </a>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 border-y border-white/10">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                className="text-center"
              >
                <div className={`text-4xl md:text-5xl font-bold bg-gradient-to-r ${stat.color} bg-clip-text text-transparent mb-2`}>
                  {stat.value}
                </div>
                <div className="text-muted-foreground">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                Enterprise Features
              </span>
            </h2>
            <p className="text-xl text-muted-foreground">
              Built for scale, optimized for performance
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <Card key={feature.title} hover gradient className="space-y-4">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                  className="w-12 h-12 rounded-lg bg-gradient-to-r from-primary to-secondary flex items-center justify-center"
                >
                  <feature.icon className="w-6 h-6 text-white" />
                </motion.div>
                <h3 className="text-xl font-bold text-foreground">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Developer Profile */}
      <section className="py-20 bg-gradient-to-b from-transparent via-primary/5 to-transparent">
        <div className="container mx-auto px-4">
          <Card className="max-w-4xl mx-auto" gradient>
            <div className="flex flex-col md:flex-row items-center gap-8">
              {/* Avatar */}
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-primary to-secondary rounded-full blur-2xl opacity-50" />
                <div className="relative w-32 h-32 rounded-full bg-gradient-to-r from-primary to-secondary flex items-center justify-center">
                  <User className="w-16 h-16 text-white" />
                </div>
              </div>

              {/* Info */}
              <div className="flex-1 text-center md:text-left">
                <h3 className="text-3xl font-bold mb-2">Rupendra Alariya</h3>
                <p className="text-xl text-primary mb-4">
                  AI Engineer • Machine Learning Engineer • Full Stack AI Developer
                </p>
                <p className="text-muted-foreground mb-4">B.Tech Computer Science (AI & ML)</p>

                {/* Skills */}
                <div className="flex flex-wrap gap-2 mb-6 justify-center md:justify-start">
                  {skills.slice(0, 8).map((skill) => (
                    <Badge key={skill} variant="default">
                      {skill}
                    </Badge>
                  ))}
                </div>

                {/* Social Links */}
                <div className="flex items-center gap-4 justify-center md:justify-start">
                  <a
                    href="https://github.com/RupendraAlariya"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-primary hover:underline"
                  >
                    <Github className="w-5 h-5" />
                    <span>GitHub</span>
                  </a>
                  <a
                    href="https://linkedin.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-primary hover:underline"
                  >
                    <Linkedin className="w-5 h-5" />
                    <span>LinkedIn</span>
                  </a>
                  <a
                    href="mailto:r44050.rupendra@jnujaipur.ac.in"
                    className="flex items-center gap-2 text-primary hover:underline"
                  >
                    <Mail className="w-5 h-5" />
                    <span>Email</span>
                  </a>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </section>

      <Footer />
    </div>
  );
}
