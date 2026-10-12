import React from 'react';
import { KPIMetrics } from '../types';
import { Trash2, AlertTriangle, Truck, Navigation, Recycle, Leaf, TrendingUp } from 'lucide-react';

interface KPIDashboardProps {
  kpis: KPIMetrics | null;
}

export const KPIDashboard: React.FC<KPIDashboardProps> = ({ kpis }) => {
  if (!kpis) return null;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
      
      {/* 1. Monitored Bins */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-1">
          <span className="text-[11px] font-medium uppercase tracking-wider">Smart Bins</span>
          <Trash2 className="w-4 h-4 text-emerald-400" />
        </div>
        <div>
          <div className="text-2xl font-bold text-white tracking-tight">{kpis.bins.total}</div>
          <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-1.5">
            <span className="text-emerald-400 font-medium">{kpis.bins.normal} normal</span>
            <span>•</span>
            <span className="text-amber-400 font-medium">{kpis.bins.warning} warn</span>
          </div>
        </div>
      </div>

      {/* 2. Critical Overflow Risk */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-1">
          <span className="text-[11px] font-medium uppercase tracking-wider">Critical (&gt;85%)</span>
          <AlertTriangle className="w-4 h-4 text-rose-400" />
        </div>
        <div>
          <div className="text-2xl font-bold text-rose-400 tracking-tight">{kpis.bins.critical}</div>
          <div className="text-[11px] text-slate-400 mt-1">
            {kpis.bins.critical > 0 ? 'Urgent dispatch required' : 'Optimal city capacity'}
          </div>
        </div>
      </div>

      {/* 3. Fleet Utilization */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-1">
          <span className="text-[11px] font-medium uppercase tracking-wider">Active Fleet</span>
          <Truck className="w-4 h-4 text-cyan-400" />
        </div>
        <div>
          <div className="text-2xl font-bold text-white tracking-tight">
            {kpis.fleet.collecting} <span className="text-sm font-normal text-slate-400">/ {kpis.fleet.total}</span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            {kpis.fleet.active} available vehicles
          </div>
        </div>
      </div>

      {/* 4. Scheduled Payload */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-1">
          <span className="text-[11px] font-medium uppercase tracking-wider">Scheduled Payload</span>
          <TrendingUp className="w-4 h-4 text-purple-400" />
        </div>
        <div>
          <div className="text-2xl font-bold text-white tracking-tight">
            {kpis.active_plan.total_waste_kg.toFixed(0)} <span className="text-xs font-normal text-slate-400">kg</span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            {kpis.active_plan.scheduled_bins} bins scheduled
          </div>
        </div>
      </div>

      {/* 5. Route Distance & CO2 Saved */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-1">
          <span className="text-[11px] font-medium uppercase tracking-wider">CO2 Saved</span>
          <Leaf className="w-4 h-4 text-emerald-400" />
        </div>
        <div>
          <div className="text-2xl font-bold text-emerald-400 tracking-tight">
            {kpis.active_plan.estimated_co2_kg.toFixed(1)} <span className="text-xs font-normal text-slate-400">kg</span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            {kpis.active_plan.total_distance_km.toFixed(1)} km CVRP route
          </div>
        </div>
      </div>

      {/* 6. Diversion & Purity */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-1">
          <span className="text-[11px] font-medium uppercase tracking-wider">Landfill Diversion</span>
          <Recycle className="w-4 h-4 text-teal-400" />
        </div>
        <div>
          <div className="text-2xl font-bold text-teal-300 tracking-tight">
            {kpis.waste.diversion_rate_pct.toFixed(1)}%
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Purity score: {kpis.waste.avg_purity_pct.toFixed(1)}%
          </div>
        </div>
      </div>

    </div>
  );
};
