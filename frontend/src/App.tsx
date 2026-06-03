import { Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import LandingPage from '@/pages/LandingPage';
import DashboardLayout from '@/layouts/DashboardLayout';
import DashboardOverview from '@/pages/DashboardOverview';
import PredictPage from '@/pages/PredictPage';
import BatchPredictPage from '@/pages/BatchPredictPage';
import AnalyticsPage from '@/pages/AnalyticsPage';
import MonitorPage from '@/pages/MonitorPage';

function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<DashboardLayout />}>
          <Route index element={<DashboardOverview />} />
          <Route path="predict" element={<PredictPage />} />
          <Route path="batch" element={<BatchPredictPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="monitor" element={<MonitorPage />} />
        </Route>
      </Routes>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: 'rgba(15, 23, 42, 0.9)',
            color: '#fff',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            backdropFilter: 'blur(12px)',
          },
          success: {
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
    </>
  );
}

export default App;
