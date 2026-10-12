import React from 'react';
import { Bot, Play, FastForward, RotateCcw, FileText, CheckCircle2, ShieldCheck } from 'lucide-react';

interface NavbarProps {
  onRunAgents: () => void;
  onSimulateTick: () => void;
  onReset: () => void;
  isRunning: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  onRunAgents,
  onSimulateTick,
  onReset,
  isRunning,
}) => {
  return (
    <header className="bg-slate-900/90 border-b border-slate-800 sticky top-0 z-50 backdrop-blur-md px-6 py-3">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        
        {/* Brand & System Status */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Bot className="w-6 h-6 text-slate-950 font-bold" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold text-white tracking-tight">EcoAgent Smart Waste OS</h1>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                8 Agents Online
              </span>
            </div>
            <p className="text-xs text-slate-400">Autonomous CVRP Routing • ML Forecasting • HITL Approval</p>
          </div>
        </div>

        {/* Global Action Bar */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={onRunAgents}
            disabled={isRunning}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow-sm ${
              isRunning
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                : 'bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-emerald-500/20 active:scale-95'
            }`}
          >
            <Play className={`w-3.5 h-3.5 ${isRunning ? 'animate-spin' : ''}`} />
            {isRunning ? 'Orchestrating...' : 'Run 8-Agent Cycle'}
          </button>

          <button
            onClick={onSimulateTick}
            className="px-3.5 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center gap-1.5 active:scale-95"
            title="Advance simulated IoT sensors forward by 1 time step"
          >
            <FastForward className="w-3.5 h-3.5 text-cyan-400" />
            IoT Telemetry Tick
          </button>

          <a
            href="/api/reports/pdf"
            target="_blank"
            rel="noopener noreferrer"
            className="px-3.5 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center gap-1.5 active:scale-95"
          >
            <FileText className="w-3.5 h-3.5 text-amber-400" />
            PDF Report
          </a>

          <button
            onClick={onReset}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800/60 hover:bg-rose-950/40 text-slate-400 hover:text-rose-300 border border-slate-800 hover:border-rose-900/40 transition flex items-center gap-1"
            title="Reset system state to default demo dataset"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset
          </button>
        </div>

      </div>
    </header>
  );
};
