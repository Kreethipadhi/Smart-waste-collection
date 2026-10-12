import React, { useState } from 'react';
import { SmartBin, WasteType, BinStatus } from '../types';
import { Search, Filter, AlertTriangle, ArrowUpDown, Zap } from 'lucide-react';

interface BinManagementProps {
  bins: SmartBin[];
  onInjectSpike: (binId: string) => void;
}

export const BinManagement: React.FC<BinManagementProps> = ({ bins, onInjectSpike }) => {
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');

  const filteredBins = bins.filter(b => {
    const matchesSearch = b.name.toLowerCase().includes(search.toLowerCase()) || b.id.toLowerCase().includes(search.toLowerCase()) || b.zone.toLowerCase().includes(search.toLowerCase());
    const matchesType = filterType === 'ALL' || b.waste_type === filterType;
    const matchesStatus = filterStatus === 'ALL' || b.status === filterStatus;
    return matchesSearch && matchesType && matchesStatus;
  });

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-xl">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight">Smart Bin Fleet & IoT Sensor Telemetry</h2>
          <p className="text-xs text-slate-400">Real-time fill monitoring, ML predictive overflow analytics, and priority rankings</p>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Search bins or zones..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
          </div>

          {/* Waste Type Filter */}
          <select
            value={filterType}
            onChange={e => setFilterType(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
          >
            <option value="ALL">All Streams</option>
            <option value="GENERAL">General</option>
            <option value="RECYCLABLE">Recyclable</option>
            <option value="ORGANIC">Organic</option>
            <option value="HAZARDOUS">Hazardous</option>
          </select>

          {/* Status Filter */}
          <select
            value={filterStatus}
            onChange={e => setFilterStatus(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="CRITICAL">Critical</option>
            <option value="WARNING">Warning</option>
            <option value="NORMAL">Normal</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 text-[11px] uppercase tracking-wider font-semibold">
              <th className="pb-3 pl-2">Bin ID & Location</th>
              <th className="pb-3">Stream</th>
              <th className="pb-3">Current Fill</th>
              <th className="pb-3">Payload (kg)</th>
              <th className="pb-3">6h Forecast</th>
              <th className="pb-3">Overflow ETA</th>
              <th className="pb-3">Priority Score</th>
              <th className="pb-3">Sensor Health</th>
              <th className="pb-3 text-right pr-2">Simulate</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-200">
            {filteredBins.map(b => (
              <tr key={b.id} className="hover:bg-slate-900/60 transition group">
                <td className="py-2.5 pl-2">
                  <div className="font-semibold text-white">{b.name}</div>
                  <div className="text-[10px] text-slate-400 font-mono">{b.id} • {b.zone}</div>
                </td>
                <td className="py-2.5">
                  <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${
                    b.waste_type === 'RECYCLABLE' ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20' :
                    b.waste_type === 'ORGANIC' ? 'bg-amber-500/10 text-amber-300 border border-amber-500/20' :
                    b.waste_type === 'HAZARDOUS' ? 'bg-purple-500/10 text-purple-300 border border-purple-500/20' : 'bg-sky-500/10 text-sky-300 border border-sky-500/20'
                  }`}>
                    {b.waste_type}
                  </span>
                </td>
                <td className="py-2.5 min-w-[120px]">
                  <div className="flex items-center justify-between text-[11px] mb-1">
                    <span className={`font-bold ${b.current_fill_pct >= 85 ? 'text-rose-400' : b.current_fill_pct >= 70 ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {b.current_fill_pct.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        b.current_fill_pct >= 85 ? 'bg-rose-500' : b.current_fill_pct >= 70 ? 'bg-amber-500' : 'bg-emerald-500'
                      }`}
                      style={{ width: `${b.current_fill_pct}%` }}
                    ></div>
                  </div>
                </td>
                <td className="py-2.5 font-medium">{b.current_weight_kg.toFixed(1)} kg</td>
                <td className="py-2.5 font-medium text-slate-300">{b.predicted_fill_6h.toFixed(1)}%</td>
                <td className="py-2.5">
                  <span className={`font-semibold ${b.hours_to_overflow <= 6 ? 'text-rose-400' : b.hours_to_overflow <= 12 ? 'text-amber-300' : 'text-slate-300'}`}>
                    {b.hours_to_overflow.toFixed(1)} hrs
                  </span>
                </td>
                <td className="py-2.5">
                  <div className="flex items-center gap-1.5">
                    <span className={`font-bold ${b.collection_priority >= 70 ? 'text-rose-400' : b.collection_priority >= 50 ? 'text-amber-300' : 'text-slate-300'}`}>
                      {b.collection_priority.toFixed(1)}
                    </span>
                    <span className="text-[10px] text-slate-500">/100</span>
                  </div>
                </td>
                <td className="py-2.5">
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                    b.sensor_health === 'OK' ? 'bg-emerald-500/10 text-emerald-400' :
                    b.sensor_health === 'TILTED' ? 'bg-purple-500/20 text-purple-300' : 'bg-rose-500/20 text-rose-300'
                  }`}>
                    {b.sensor_health}
                  </span>
                </td>
                <td className="py-2.5 text-right pr-2">
                  <button
                    onClick={() => onInjectSpike(b.id)}
                    className="p-1 rounded bg-slate-800 hover:bg-rose-950 text-slate-400 hover:text-rose-300 border border-slate-700 transition"
                    title="Simulate sudden overfill spike on this bin"
                  >
                    <Zap className="w-3.5 h-3.5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
