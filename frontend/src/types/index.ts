export type WasteType = 'GENERAL' | 'RECYCLABLE' | 'ORGANIC' | 'HAZARDOUS';

export type BinStatus = 'NORMAL' | 'WARNING' | 'CRITICAL' | 'OFFLINE' | 'MAINTENANCE';

export type SensorHealth = 'OK' | 'ANOMALOUS' | 'STALE' | 'SPIKE' | 'DRIFT' | 'TILTED';

export type VehicleStatus = 'IDLE' | 'EN_ROUTE' | 'COLLECTING' | 'RETURNING_TO_DEPOT' | 'MAINTENANCE';

export type ApprovalStatus = 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'MODIFIED' | 'EXECUTING' | 'COMPLETED';

export interface SmartBin {
  id: string;
  name: string;
  zone: string;
  latitude: number;
  longitude: number;
  waste_type: WasteType;
  capacity_kg: number;
  current_fill_pct: number;
  current_weight_kg: number;
  battery_pct: number;
  temperature_c: number;
  tilt_angle_deg: number;
  sensor_health: SensorHealth;
  status: BinStatus;
  last_collected_at?: string;
  last_reading_at?: string;
  predicted_fill_6h: number;
  predicted_fill_12h: number;
  predicted_fill_24h: number;
  hours_to_overflow: number;
  collection_priority: number;
  priority_reasons: string[];
  anomaly_flags: string[];
  recycling_purity_pct: number;
  contamination_pct: number;
}

export interface Vehicle {
  id: string;
  name: string;
  model: string;
  status: VehicleStatus;
  latitude: number;
  longitude: number;
  supported_waste_types: WasteType[];
  max_payload_kg: number;
  current_payload_kg: number;
  fuel_level_pct: number;
  efficiency_km_per_liter: number;
  current_route_id?: string;
}

export interface RouteWaypoint {
  bin_id?: string;
  name: string;
  latitude: number;
  longitude: number;
  action: string;
  waste_amount_kg: number;
  cumulative_weight_kg: number;
  estimated_arrival_minutes: number;
}

export interface VehicleRoute {
  route_id: string;
  vehicle_id: string;
  vehicle_name: string;
  waste_type: WasteType;
  waypoints: RouteWaypoint[];
  bin_ids: string[];
  total_distance_km: number;
  estimated_duration_min: number;
  total_waste_kg: number;
  capacity_utilization_pct: number;
}

export interface CollectionPlan {
  plan_id: string;
  created_at: string;
  status: ApprovalStatus;
  routes: VehicleRoute[];
  total_bins_scheduled: number;
  total_waste_kg: number;
  total_distance_km: number;
  estimated_co2_kg: number;
  approver_notes?: string;
  reviewed_by?: string;
  critic_review?: {
    critic_score: number;
    is_valid: boolean;
    violations: string[];
    warnings: string[];
    checks_passed: string[];
    recommendation: string;
  };
}

export interface AgentLogEntry {
  id: string;
  timestamp: string;
  agent_name: string;
  action: string;
  details: Record<string, any>;
  level: 'INFO' | 'WARNING' | 'ALERT' | 'SUCCESS';
}

export interface KPIMetrics {
  bins: {
    total: number;
    critical: number;
    warning: number;
    normal: number;
  };
  fleet: {
    total: number;
    active: number;
    collecting: number;
  };
  waste: {
    total_field_kg: number;
    diversion_rate_pct: number;
    avg_purity_pct: number;
  };
  active_plan: {
    plan_id: string | null;
    status: string;
    scheduled_bins: number;
    total_distance_km: number;
    total_waste_kg: number;
    estimated_co2_kg: number;
  };
}

export interface CVAnalysisResult {
  bin_id: string;
  waste_type: string;
  detected_items: Array<{
    label: string;
    confidence: number;
    category: string;
    is_contaminant: boolean;
  }>;
  contamination_pct: number;
  purity_score_pct: number;
  is_contaminated: boolean;
  recommendation: string;
  model_version: string;
}
