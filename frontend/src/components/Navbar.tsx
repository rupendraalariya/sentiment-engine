import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Brain, Github, Linkedin, Mail } from 'lucide-react';
import Button from './Button';
import { useApiStatus } from '@/hooks/useApiStatus';

const Navbar = () => {
  const location = useLocation();
  const { data: status } = useApiStatus();
  const isOnline = status?.status === 'healthy';

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className="fixed top-0 left-0 right-0 z-50 glass-strong border-b border-white/10"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-3 group">
            <motion.div
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.6 }}
              className="bg-gradient-to-r from-primary to-secondary p-2 rounded-lg"
            >
              <Brain className="h-6 w-6 text-white" />
            </motion.div>
            <span className="text-xl font-bold gradient-text">
              Sentiment Engine
            </span>
          </Link>

          <div className="flex items-center space-x-6">
            <div className="hidden md:flex items-center space-x-1">
              <Link to="/">
                <Button variant="ghost" size="sm">
                  Home
                </Button>
              </Link>
              <Link to="/dashboard">
                <Button variant="ghost" size="sm">
                  Dashboard
                </Button>
              </Link>
              <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">
                <Button variant="ghost" size="sm">
                  API Docs
                </Button>
              </a>
            </div>

            <div className="flex items-center space-x-3">
              <a
                href="https://github.com/RupendraAlariya"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-white transition-colors"
              >
                <Github className="h-5 w-5" />
              </a>
              <a
                href="https://linkedin.com/in/rupendra-alariya"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-white transition-colors"
              >
                <Linkedin className="h-5 w-5" />
              </a>
              <a
                href="mailto:r44050.rupendra@jnujaipur.ac.in"
                className="text-muted-foreground hover:text-white transition-colors"
              >
                <Mail className="h-5 w-5" />
              </a>
            </div>

            <div className="flex items-center space-x-2">
              <div className={`h-2 w-2 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
              <span className="text-xs text-muted-foreground">
                {isOnline ? 'Online' : 'Offline'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </motion.nav>
  );
};

export default Navbar;
