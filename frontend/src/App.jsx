import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Navbar } from './components/Navbar';
import { GISMap } from './components/GISMap';
import { AIRoutePlanner } from './components/AIRoutePlanner';
import { VehicleTracker } from './components/VehicleTracker';
import { FieldReporter } from './components/FieldReporter';
import { AnalyticsDashboard } from './components/AnalyticsDashboard';
import { AlertCenter } from './components/AlertCenter';
import { NewsCenter } from './components/NewsCenter';
import { LoginPage } from './components/LoginPage';
import './styles/index.css';

const MainContentSwitcher = () => {
  const { activeTab } = useApp();

  return (
    <main className="main-content">
      {activeTab === 'map' && <GISMap />}
      {activeTab === 'planner' && <AIRoutePlanner />}
      {activeTab === 'fleet' && <VehicleTracker />}
      {activeTab === 'incidents' && <FieldReporter />}
      {activeTab === 'analytics' && <AnalyticsDashboard />}
      {activeTab === 'alerts' && <AlertCenter />}
      {activeTab === 'news' && <NewsCenter />}
    </main>
  );
};

const AppShell = () => {
  const { isAuthenticated } = useApp();

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <div className="app-wrapper">
      <Navbar />
      <MainContentSwitcher />
    </div>
  );
};

export default function App() {
  return (
    <ErrorBoundary>
      <AppProvider>
        <AppShell />
      </AppProvider>
    </ErrorBoundary>
  );
}

