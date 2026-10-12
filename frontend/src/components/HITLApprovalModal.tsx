import React, { useState } from 'react';
import { CollectionPlan } from '../types';
import { ShieldCheck, Check, X, Send, CheckCircle2, AlertTriangle, FileText, Truck, ArrowRight } from 'lucide-react';

interface HITLApprovalModalProps {
  plan: CollectionPlan | null;
  onAction: (action: 'APPROVE' | 'REJECT' | 'MODIFY' | 'DISPATCH' | 'COMPLETE', notes?: string) => void;
  isActionLoading: boolean;
}

export const HITLApprovalModal: React.FC<HITLApprovalModalProps> = ({
  plan,
  onAction,
  isActionLoading,
}) => {
  const [notes, setNotes] = useState('');
  const [showRejectInput, setShowRejectInput] = useState(false);

  if (!plan) return null;

  const isPending = plan.status === 'PENDING_APPROVAL';
  const isApproved = plan.status === 'APPROVED';
  const isExecuting = plan.status === 'EXECUTING';
  const isCompleted = plan.status === 'COMPLETED';

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-xl mb-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800 pb-4 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h2 className="text-base font-bold text-white tracking-tight">Human-in-the-Loop (HITL) Operations Gate</h2>
            <span className={`text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${
              isPending ? 'bg-amber-500/10 text-amber-400 border-amber-500/30 animate-pulse' :
              isApproved ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
              isExecuting ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' :
              isCompleted ? 'bg-purple-500/10 text-purple-400 border-purple-500/30' : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
            }`}>
              {plan.status.replace('_', ' ')}
            </span>
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Plan ID: <span className="font-mono text-slate-300">{plan.plan_id}</span> • Created: {new Date(plan.created_at).toLocaleTimeString()}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {isPending && (
            <>
              <button
                onClick={() => onAction('APPROVE', notes)}
                disabled={isActionLoading}
                className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition flex items-center gap-1.5 shadow-sm active:scale-95 disabled:opacity-50"
              >
                <Check className="w-3.5 h-3.5" />
                Approve Plan
              </button>
              <button
                onClick={() => {
                  if (!showRejectInput) setShowRejectInput(true);
                  else onAction('REJECT', notes || 'Manual supervisor rejection');
                }}
                disabled={isActionLoading}
                className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800 transition flex items-center gap-1.5 active:scale-95 disabled:opacity-50"
              >
                <X className="w-3.5 h-3.5" />
                Reject Plan
              </button>
            </>
          )}

          {isApproved && (
            <button
              onClick={() => onAction('DISPATCH')}
              disabled={isActionLoading}
              className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition flex items-center gap-1.5 shadow-sm active:scale-95 disabled:opacity-50"
            >
              <Truck className="w-3.5 h-3.5" />
              Dispatch Fleet
            </button>
          )}

          {isExecuting && (
            <button
              onClick={() => onAction('COMPLETE')}
              disabled={isActionLoading}
              className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-purple-500 hover:bg-purple-400 text-slate-950 transition flex items-center gap-1.5 shadow-sm active:scale-95 disabled:opacity-50"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              Simulate Completion & Empty Bins
            </button>
          )}

          <a
            href="/api/reports/pdf"
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center gap-1.5 active:scale-95"
          >
            <FileText className="w-3.5 h-3.5 text-amber-400" />
            Download PDF
          </a>
        </div>
      </div>

      {showRejectInput && isPending && (
        <div className="mb-4 p-3 bg-slate-950 border border-rose-900/60 rounded-xl flex items-center gap-2">
          <input
            type="text"
            placeholder="Reason for plan rejection (e.g., Road closure on Market St, reschedule for 14:00)..."
            value={notes}
            onChange={e => setNotes(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 w-full focus:outline-none focus:border-rose-500"
          />
          <button
            onClick={() => onAction('REJECT', notes)}
            className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-bold shrink-0"
          >
            Confirm Rejection
          </button>
        </div>
      )}

      {/* Critic Review Box */}
      {plan.critic_review && (
        <div className="mb-4 p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-3">
            <div className={`w-9 h-9 rounded-lg flex items-center justify-center font-bold text-sm ${
              plan.critic_review.is_valid ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
            }`}>
              {plan.critic_review.critic_score}
            </div>
            <div>
              <div className="font-semibold text-slate-200">
                Agent 8 Critic Audit: {plan.critic_review.is_valid ? 'All Constraints Passed' : 'Violations Flagged'}
              </div>
              <div className="text-slate-400 text-[11px]">
                {plan.critic_review.violations.length} overload violations • {plan.critic_review.warnings.length} SLA warnings
              </div>
            </div>
          </div>
          <div className="text-slate-300 font-medium text-[11px] bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
            {plan.critic_review.recommendation}
          </div>
        </div>
      )}

      {/* Route Breakdown Cards */}
      <div className="space-y-3">
        <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Dispatched CVRP Routes ({plan.routes.length})
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {plan.routes.map(r => (
            <div key={r.route_id} className="bg-slate-950 rounded-xl border border-slate-800 p-3 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="font-semibold text-white text-xs">{r.vehicle_name}</div>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded uppercase bg-slate-800 text-sky-400 border border-slate-700">
                    {r.waste_type}
                  </span>
                </div>

                <div className="space-y-1.5 text-xs text-slate-300">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Total Waypoints:</span>
                    <span className="font-medium text-slate-200">{r.bin_ids.length} bins</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Distance:</span>
                    <span className="font-medium text-slate-200">{r.total_distance_km.toFixed(1)} km</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Est. Duration:</span>
                    <span className="font-medium text-slate-200">{r.estimated_duration_min.toFixed(0)} min</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Total Waste Payload:</span>
                    <span className="font-medium text-cyan-400">{r.total_waste_kg.toFixed(1)} kg</span>
                  </div>
                </div>

                {/* Utilization Progress Bar */}
                <div className="mt-3">
                  <div className="flex justify-between text-[11px] mb-1">
                    <span className="text-slate-400">Capacity Utilization</span>
                    <span className="font-bold text-slate-200">{r.capacity_utilization_pct.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        r.capacity_utilization_pct > 90 ? 'bg-amber-400' : 'bg-emerald-400'
                      }`}
                      style={{ width: `${r.capacity_utilization_pct}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              {/* Waypoint Sequence */}
              <div className="mt-3 pt-2 border-t border-slate-900 text-[10px] text-slate-500 truncate">
                Waypoints: Depot → {r.bin_ids.join(' → ')} → Depot
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
