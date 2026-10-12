import { SmartBin, Vehicle, CollectionPlan, AgentLogEntry, KPIMetrics, CVAnalysisResult } from '../types';

const API_BASE = '/api';

export const api = {
  async getKPIs(): Promise<KPIMetrics> {
    const res = await fetch(`${API_BASE}/kpis`);
    return res.json();
  },

  async getBins(): Promise<SmartBin[]> {
    const res = await fetch(`${API_BASE}/bins`);
    return res.json();
  },

  async getVehicles(): Promise<Vehicle[]> {
    const res = await fetch(`${API_BASE}/vehicles`);
    return res.json();
  },

  async getActivePlan(): Promise<CollectionPlan> {
    const res = await fetch(`${API_BASE}/plans/active`);
    return res.json();
  },

  async runAgents(): Promise<any> {
    const res = await fetch(`${API_BASE}/agents/run`, { method: 'POST' });
    return res.json();
  },

  async getAgentLogs(limit = 40): Promise<AgentLogEntry[]> {
    const res = await fetch(`${API_BASE}/agents/logs?limit=${limit}`);
    return res.json();
  },

  async simulateTick(): Promise<any> {
    const res = await fetch(`${API_BASE}/sensors/simulate-tick`, { method: 'POST' });
    return res.json();
  },

  async injectSpike(binId: string, fillPct = 98.0): Promise<any> {
    const res = await fetch(`${API_BASE}/sensors/inject-spike`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bin_id: binId, target_fill_pct: fillPct }),
    });
    return res.json();
  },

  async planAction(action: 'APPROVE' | 'REJECT' | 'MODIFY' | 'DISPATCH' | 'COMPLETE', notes?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/plans/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, notes }),
    });
    return res.json();
  },

  async triggerReplan(triggerType: string, targetBinId?: string, failedVehicleId?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/agents/replan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        trigger_type: triggerType,
        target_bin_id: targetBinId,
        failed_vehicle_id: failedVehicleId,
      }),
    });
    return res.json();
  },

  async analyzeCV(binId: string, sampleType = 'clean_recyclables'): Promise<CVAnalysisResult> {
    const res = await fetch(`${API_BASE}/recycling/cv-analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bin_id: binId, sample_type: sampleType }),
    });
    return res.json();
  },

  async resetSystem(): Promise<any> {
    const res = await fetch(`${API_BASE}/kpis/reset`, { method: 'POST' });
    return res.json();
  },

  getReportPdfUrl(): string {
    return `${API_BASE}/reports/pdf`;
  },
};
