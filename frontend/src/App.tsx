import React, { useState, useEffect } from 'react';
import { SmartBin, Vehicle, CollectionPlan, AgentLogEntry, KPIMetrics } from './types';
import { api } from './services/api';
import { Navbar } from './components/Navbar';
import { KPIDashboard } from './components/KPIDashboard';
import { GISMap } from './components/GISMap';
import { HITLApprovalModal } from './components/HITLApprovalModal';
import { AgentVisualizer } from './components/AgentVisualizer';
import { DynamicReplanPanel } from './components/DynamicReplanPanel';
import { RecyclingCVInspector } from './components/RecyclingCVInspector';
import { BinManagement } from './components/BinManagement';
import { MapPin, Cpu, Eye, Zap, ListFilter } from 'lucide-react';

export const App: React.FC = () => {
  const [kpis, setKpis] = useState<KPIMetrics | null>(null);
  const [bins, setBins] = useState<SmartBin[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [plan, setPlan] = useState<CollectionPlan | null>(null);
  const [logs, setLogs] = useState<AgentLogEntry[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'map' | 'bins' | 'vision' | 'replan'>('map');

  const fetchState = async () => {
    try {
      const [kpisData, binsData, vehiclesData, planData, logsData] = await Promise.all([
        api.getKPIs(),
        api.getBins(),
        api.getVehicles(),
        api.getActivePlan(),
        api.getAgentLogs(50),
      ]);
      setKpis(kpisData);
      setBins(binsData);
      setVehicles(vehiclesData);
      setPlan(planData);
      setLogs(logsData);
    } catch (err) {
      console.error('Failed to load system state:', err);
    }
  };

  useEffect(() => {
    fetchState();
    const interval = setInterval(fetchState, 6000);
    return () => clearInterval(interval);
  }, []);

  const handleRunAgents = async () => {
    setIsRunning(true);
    try {
      await api.runAgents();
      await fetchState();
    } catch (err) {
      console.error('Error running multi-agent cycle:', err);
    } finally {
      setIsRunning(false);
    }
  };

  const handleSimulateTick = async () => {
    try {
      await api.simulateTick();
      await fetchState();
    } catch (err) {
      console.error('Error simulating IoT telemetry tick:', err);
    }
  };

  const handleReset = async () => {
    try {
      await api.resetSystem();
      await fetchState();
    } catch (err) {
      console.error('Error resetting system:', err);
    }
  };

  const handlePlanAction = async (
    action: 'APPROVE' | 'REJECT' | 'MODIFY' | 'DISPATCH' | 'COMPLETE',
    notes?: string
  ) => {
    setIsActionLoading(true);
    try {
      await api.planAction(action, notes);
      await fetchState();
    } catch (err) {
      console.error(`Error applying action ${action}:`, err);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleTriggerReplan = async (
    triggerType: string,
    targetBinId?: string,
    failedVehicleId?: string
  ) => {
    setIsRunning(true);
    try {
      await api.triggerReplan(triggerType, targetBinId, failedVehicleId);
      await fetchState();
    } catch (err) {
      console.error('Error triggering dynamic replanning:', err);
    } finally {
      setIsRunning(false);
    }
  };

  const handleInjectSpike = async (binId: string) => {
    try {
      await api.injectSpike(binId, 99.0);
      await fetchState();
    } catch (err) {
      console.error('Error injecting spike:', err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation */}
      <Navbar
        onRunAgents={handleRunAgents}
        onSimulateTick={handleSimulateTick}
        onReset={handleReset}
        isRunning={isRunning}
      />

      {/* Main Operations Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 space-y-6">
        
        {/* Executive KPI Metrics */}
        <KPIDashboard kpis={kpis} />

        {/* Human-in-the-Loop Approval & Operations Gate */}
        <HITLApprovalModal
          plan={plan}
          onAction={handlePlanAction}
          isActionLoading={isActionLoading}
        />

        {/* Workspace Tab Bar */}
        <div className="flex border-b border-slate-800 space-x-1 pb-1">
          <button
            onClick={() => setActiveTab('map')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition ${
              activeTab === 'map'
                ? 'bg-slate-900 text-emerald-400 border border-slate-800 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
            }`}
          >
            <MapPin className="w-4 h-4" />
            Interactive GIS Map & CVRP Routes
          </button>

          <button
            onClick={() => setActiveTab('bins')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition ${
              activeTab === 'bins'
                ? 'bg-slate-900 text-emerald-400 border border-slate-800 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
            }`}
          >
            <ListFilter className="w-4 h-4" />
            Smart Bins & Telemetry ({bins.length})
          </button>

          <button
            onClick={() => setActiveTab('vision')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition ${
              activeTab === 'vision'
                ? 'bg-slate-900 text-teal-400 border border-slate-800 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
            }`}
          >
            <Eye className="w-4 h-4" />
            AI Computer Vision Inspector
          </button>

          <button
            onClick={() => setActiveTab('replan')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition ${
              activeTab === 'replan'
                ? 'bg-slate-900 text-amber-400 border border-slate-800 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
            }`}
          >
            <Zap className="w-4 h-4" />
            Dynamic Edge Replanner
          </button>
        </div>

        {/* Active Tab View */}
        <div>
          {activeTab === 'map' && (
            <GISMap
              bins={bins}
              vehicles={vehicles}
              plan={plan}
              onInjectSpike={handleInjectSpike}
            />
          )}

          {activeTab === 'bins' && (
            <BinManagement
              bins={bins}
              onInjectSpike={handleInjectSpike}
            />
          )}

          {activeTab === 'vision' && (
            <RecyclingCVInspector binId="BIN-005" />
          )}

          {activeTab === 'replan' && (
            <DynamicReplanPanel
              bins={bins}
              vehicles={vehicles}
              onTriggerReplan={handleTriggerReplan}
              isLoading={isRunning}
            />
          )}
        </div>

        {/* Autonomous Multi-Agent Orchestrator & Live Reasoning Logs */}
        <AgentVisualizer logs={logs} isRunning={isRunning} />

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 px-6 py-4 text-center text-xs text-slate-500">
        EcoAgent Smart Waste Optimization System • Powered by Google OR-Tools CVRP, Scikit-Learn ML Forecasting, and Multi-Agent AI
      </footer>
    </div>
  );
};

export default App;
