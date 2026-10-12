import React, { useState } from 'react';
import { AgentLogEntry } from '../types';
import { Bot, Terminal, ShieldCheck, Activity, Cpu, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

interface AgentVisualizerProps {
  logs: AgentLogEntry[];
  isRunning: boolean;
}

const AGENTS = [
  { id: 'agent-1', name: 'Smart Bin Monitoring Agent', role: 'IoT Ingestion & Anomaly Audit', icon: '📡' },
  { id: 'agent-2', name: 'Waste Generation Forecasting Agent', role: 'Ridge ML Overflow Forecasting', icon: '📈' },
  { id: 'agent-3', name: 'Collection Priority Agent', role: 'Multi-Criteria Urgency Scoring', icon: '⚡' },
  { id: 'agent-4', name: 'Vehicle & Capacity Management Agent', role: 'Payload & Compatibility Check', icon: '🚛' },
  { id: 'agent-5', name: 'Route Optimization Agent', role: 'Google OR-Tools CVRP Synthesis', icon: '🗺️' },
  { id: 'agent-6', name: 'Recycling & Waste Segregation Agent', role: 'Purity & YOLOv8 Computer Vision', icon: '♻️' },
  { id: 'agent-7', name: 'Operations Reviewer / Critic Agent', role: 'SLA Watchdog & Plan Verification', icon: '🛡️' },
  { id: 'agent-8', name: 'Waste Operations & Action Planning Agent', role: 'HITL Gate & Fleet Dispatching', icon: '📋' },
];

export const AgentVisualizer: React.FC<AgentVisualizerProps> = ({ logs, isRunning }) => {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  const filteredLogs = selectedAgent
    ? logs.filter(l => l.agent_name.toLowerCase().includes(selectedAgent.toLowerCase()))
    : logs;

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-xl">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800/80 pb-3">
        <div className="flex items-center space-x-2.5">
          <Cpu className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-bold text-white tracking-tight">Autonomous Multi-Agent Orchestration</h2>
        </div>
        <div className="flex items-center gap-2">
          {isRunning && (
            <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
              <RefreshCw className="w-3 h-3 animate-spin" />
              Agent Workflow Active
            </span>
          )}
          <span className="text-xs text-slate-400 font-mono">8 Specialized Agents</span>
        </div>
      </div>

      {/* 8-Agent Pipeline Flow Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 mb-5">
        {AGENTS.map((agent, idx) => {
          const isSelected = selectedAgent === agent.name;
          return (
            <button
              key={agent.id}
              onClick={() => setSelectedAgent(isSelected ? null : agent.name)}
              className={`text-left p-3 rounded-xl border transition relative overflow-hidden group ${
                isSelected
                  ? 'bg-emerald-950/40 border-emerald-500/60 shadow-lg shadow-emerald-950/50'
                  : 'bg-slate-950/60 border-slate-800/90 hover:border-slate-700 hover:bg-slate-900/50'
              }`}
            >
              <div className="flex items-start justify-between mb-1.5">
                <span className="text-xl">{agent.icon}</span>
                <span className="text-[10px] font-mono text-slate-500 group-hover:text-slate-400">
                  Step {idx + 1}
                </span>
              </div>
              <div className="text-xs font-semibold text-slate-100 group-hover:text-emerald-300 transition line-clamp-1">
                {agent.name}
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5 line-clamp-1">
                {agent.role}
              </div>
              <div className="mt-2 flex items-center gap-1 text-[10px] text-emerald-400 font-medium">
                <CheckCircle2 className="w-2.5 h-2.5" />
                <span>Ready & Active</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Agent Execution Logs / Audit Terminal */}
      <div className="bg-slate-950 rounded-xl border border-slate-800 p-3.5">
        <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800/60 text-xs">
          <div className="flex items-center gap-2 text-slate-300 font-mono">
            <Terminal className="w-3.5 h-3.5 text-cyan-400" />
            <span>Agent Reasoning Audit Trail</span>
            {selectedAgent && (
              <span className="text-xs text-emerald-400 font-medium bg-emerald-500/10 px-2 py-0.5 rounded">
                Filtered: {selectedAgent}
              </span>
            )}
          </div>
          <span className="text-[11px] text-slate-500">{filteredLogs.length} events logged</span>
        </div>

        <div className="max-h-56 overflow-y-auto space-y-1.5 font-mono text-xs pr-1">
          {filteredLogs.length === 0 ? (
            <div className="text-slate-500 italic py-3 text-center">No agent audit logs recorded yet.</div>
          ) : (
            filteredLogs.map(entry => (
              <div
                key={entry.id}
                className="flex items-start gap-2 py-1 px-2 rounded hover:bg-slate-900/60 border border-transparent hover:border-slate-800 transition"
              >
                <span className="text-[10px] text-slate-500 shrink-0">
                  {new Date(entry.timestamp).toLocaleTimeString()}
                </span>
                <span className={`text-[10px] uppercase font-bold px-1 rounded shrink-0 ${
                  entry.level === 'ALERT' ? 'bg-rose-500/20 text-rose-400' :
                  entry.level === 'WARNING' ? 'bg-amber-500/20 text-amber-400' :
                  entry.level === 'SUCCESS' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-sky-500/20 text-sky-400'
                }`}>
                  {entry.level}
                </span>
                <span className="text-emerald-400 font-semibold shrink-0">[{entry.agent_name}]</span>
                <span className="text-slate-200">{entry.action}:</span>
                <span className="text-slate-400 truncate">
                  {JSON.stringify(entry.details)}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
