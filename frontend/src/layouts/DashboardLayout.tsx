import { Outlet, Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  MessageSquare,
  ListChecks,
  BarChart3,
  Activity,
  User,
} from 'lucide-react';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import { cn } from '@/utils/cn';

const sidebarItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Overview' },
  { path: '/dashboard/predict', icon: MessageSquare, label: 'Predict' },
  { path: '/dashboard/batch', icon: ListChecks, label: 'Batch Predict' },
  { path: '/dashboard/analytics', icon: BarChart3, label: 'Analytics' },
  { path: '/dashboard/monitor', icon: Activity, label: 'Monitor' },
];

const DashboardLayout = () => {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/10">
      <Navbar />
      
      <div className="flex pt-16">
        <aside className="hidden lg:block w-64 fixed left-0 top-16 bottom-0 glass-strong border-r border-white/10">
          <nav className="p-4 space-y-2">
            {sidebarItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link key={item.path} to={item.path}>
                  <motion.div
                    whileHover={{ x: 4 }}
                    className={cn(
                      'flex items-center space-x-3 px-4 py-3 rounded-lg transition-all',
                      isActive
                        ? 'bg-gradient-to-r from-primary to-secondary text-white shadow-lg'
                        : 'text-muted-foreground hover:bg-white/10 hover:text-white'
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    <span className="font-medium">{item.label}</span>
                  </motion.div>
                </Link>
              );
            })}
            
            <div className="pt-4 mt-4 border-t border-white/10">
              <Link to="/">
                <motion.div
                  whileHover={{ x: 4 }}
                  className="flex items-center space-x-3 px-4 py-3 rounded-lg text-muted-foreground hover:bg-white/10 hover:text-white transition-all"
                >
                  <User className="h-5 w-5" />
                  <span className="font-medium">Developer</span>
                </motion.div>
              </Link>
            </div>
          </nav>
        </aside>
        
        <main className="flex-1 lg:ml-64 p-8">
          <Outlet />
        </main>
      </div>
      
      <Footer />
    </div>
  );
};

export default DashboardLayout;
