import React, { useState } from 'react';
import { SmartBin, Vehicle } from '../types';
import { AlertCircle, Wrench, RefreshCw, Zap, Flame } from 'lucide-react';

interface DynamicReplanPanelProps {
  bins: SmartBin[];
  vehicles: Vehicle[];
  onTriggerReplan: (triggerType: string, targetBinId?: string, failedVehicleId?: string) => void;
  isLoading: boolean;
}

export const DynamicReplanPanel: React.FC<DynamicReplanPanelProps> = ({
  bins,
  vehicles,
  onTriggerReplan,
  isLoading,
}) => {
  const [selectedBinId, setSelectedBinId] = useState(bins[3]?.id || 'BIN-004');
  const [selectedVehicleId, setSelectedVehicleId] = useState(vehicles[0]?.id || 'VEH-101');

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-xl">
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-3 mb-4">
        <Zap className="w-5 h-5 text-amber-400" />
        <h2 className="text-base font-bold text-white tracking-tight">Dynamic Edge Replanning Simulator</h2>
      </div>

      <p className="text-xs text-slate-400 mb-4">
        Test autonomous multi-agent reactivity when unexpected field incidents occur in real-time.
        The system will autonomously re-optimize CVRP routes and update the operational manifest.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* Scenario 1: Sudden Emergency Overflow */}
        <div className="bg-slate-950 rounded-xl border border-slate-800 p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2 text-xs font-bold text-rose-400 uppercase tracking-wider">
              <Flame className="w-4 h-4" />
              Scenario A: Emergency Overfill Spike
            </div>
            <p className="text-xs text-slate-400 mb-3">
              Simulate an unexpected surge (e.g. tourist crowd, festival) pushing a normal bin to 99% fill.
            </p>

            <label className="text-[11px] text-slate-400 font-medium block mb-1">Target Smart Bin:</label>
            <select
              value={selectedBinId}
              onChange={e => setSelectedBinId(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 mb-3 focus:outline-none focus:border-rose-500"
            >
              {bins.map(b => (
                <option key={b.id} value={b.id}>
                  {b.id} - {b.name} ({b.current_fill_pct.toFixed(0)}% fill)
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => onTriggerReplan('CRITICAL_BIN', selectedBinId)}
            disabled={isLoading}
            className="w-full py-2 bg-rose-600/90 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition active:scale-95 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            Trigger Emergency Spike & Replan
          </button>
        </div>

        {/* Scenario 2: Vehicle Mechanical Breakdown */}
        <div className="bg-slate-950 rounded-xl border border-slate-800 p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2 text-xs font-bold text-amber-400 uppercase tracking-wider">
              <Wrench className="w-4 h-4" />
              Scenario B: Vehicle Breakdown / Fleet Deficit
            </div>
            <p className="text-xs text-slate-400 mb-3">
              Simulate sudden mechanical failure. Takes truck offline and dynamically redistributes its bins.
            </p>

            <label className="text-[11px] text-slate-400 font-medium block mb-1">Impacted Fleet Vehicle:</label>
            <select
              value={selectedVehicleId}
              onChange={e => setSelectedVehicleId(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 mb-3 focus:outline-none focus:border-amber-500"
            >
              {vehicles.map(v => (
                <option key={v.id} value={v.id}>
                  {v.id} - {v.name} ({v.status})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => onTriggerReplan('VEHICLE_BREAKDOWN', undefined, selectedVehicleId)}
            disabled={isLoading}
            className="w-full py-2 bg-amber-600/90 hover:bg-amber-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition active:scale-95 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            Take Vehicle Offline & Re-route
          </button>
        </div>

      </div>
    </div>
  );
};
