import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { SmartBin, Vehicle, CollectionPlan } from '../types';

interface GISMapProps {
  bins: SmartBin[];
  vehicles: Vehicle[];
  plan: CollectionPlan | null;
  onSelectBin?: (bin: SmartBin) => void;
  onInjectSpike?: (binId: string) => void;
}

const ROUTE_COLORS: Record<string, string> = {
  GENERAL: '#38bdf8', // sky blue
  RECYCLABLE: '#34d399', // emerald
  ORGANIC: '#fbbf24', // amber
  HAZARDOUS: '#c084fc', // purple
};

export const GISMap: React.FC<GISMapProps> = ({
  bins,
  vehicles,
  plan,
  onSelectBin,
  onInjectSpike,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Dark carto / openstreetmap tiles
    const map = L.map(mapContainerRef.current, {
      center: [37.7865, -122.402],
      zoom: 14,
      zoomControl: true,
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(map);

    const layerGroup = L.layerGroup().addTo(map);
    mapInstanceRef.current = map;
    layerGroupRef.current = layerGroup;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update Layers when bins, vehicles, or plan changes
  useEffect(() => {
    if (!mapInstanceRef.current || !layerGroupRef.current) return;
    const layers = layerGroupRef.current;
    layers.clearLayers();

    // 1. Depot Marker
    const depotIcon = L.divIcon({
      className: 'custom-depot-marker',
      html: `
        <div style="background:#0f172a; border:2px solid #38bdf8; color:#38bdf8; border-radius:8px; width:34px; height:34px; display:flex; align-items:center; justify-content:center; box-shadow:0 0 14px rgba(56,189,248,0.5); font-weight:bold; font-size:16px;">
          🏢
        </div>
      `,
      iconSize: [34, 34],
      iconAnchor: [17, 17],
    });

    L.marker([37.7840, -122.4010], { icon: depotIcon })
      .bindPopup(`
        <div class="p-2 text-xs">
          <div class="font-bold text-sky-400 text-sm mb-1">Central City Eco-Depot</div>
          <div class="text-slate-300">Fleet Operations Hub & Main Discharge Station</div>
          <div class="text-slate-400 text-[10px] mt-1">Starting point for all CVRP collection routes</div>
        </div>
      `)
      .addTo(layers);

    // 2. Materials Recovery Facility (MRF)
    const mrfIcon = L.divIcon({
      className: 'custom-mrf-marker',
      html: `
        <div style="background:#0f172a; border:2px solid #34d399; color:#34d399; border-radius:8px; width:34px; height:34px; display:flex; align-items:center; justify-content:center; box-shadow:0 0 14px rgba(52,211,153,0.5); font-weight:bold; font-size:16px;">
          ♻️
        </div>
      `,
      iconSize: [34, 34],
      iconAnchor: [17, 17],
    });

    L.marker([37.7910, -122.3920], { icon: mrfIcon })
      .bindPopup(`
        <div class="p-2 text-xs">
          <div class="font-bold text-emerald-400 text-sm mb-1">Bay Area MRF Recycling Plant</div>
          <div class="text-slate-300">Materials Recovery & Sorting Processing Center</div>
        </div>
      `)
      .addTo(layers);

    // 3. Draw CVRP Polyline Routes
    if (plan && plan.routes) {
      plan.routes.forEach((route, idx) => {
        const color = ROUTE_COLORS[route.waste_type] || '#38bdf8';
        const coords: [number, number][] = route.waypoints.map(wp => [wp.latitude, wp.longitude]);

        if (coords.length > 1) {
          // Route polyline with directional style
          const polyline = L.polyline(coords, {
            color: color,
            weight: 4,
            opacity: 0.85,
            dashArray: idx % 2 === 1 ? '6, 6' : undefined,
          }).addTo(layers);

          polyline.bindTooltip(
            `<b>${route.vehicle_name}</b><br/>Stream: ${route.waste_type}<br/>Distance: ${route.total_distance_km} km | Payload: ${route.total_waste_kg} kg`,
            { sticky: true }
          );

          // Add waypoint numbering badges
          route.waypoints.forEach((wp, wIdx) => {
            if (wp.action === 'COLLECT') {
              const stopBadge = L.divIcon({
                className: 'stop-badge',
                html: `
                  <div style="background:${color}; color:#090d16; font-size:10px; font-weight:bold; border-radius:9999px; width:18px; height:18px; display:flex; align-items:center; justify-content:center; box-shadow:0 0 6px ${color};">
                    ${wIdx}
                  </div>
                `,
                iconSize: [18, 18],
                iconAnchor: [9, 9],
              });
              L.marker([wp.latitude, wp.longitude], { icon: stopBadge }).addTo(layers);
            }
          });
        }
      });
    }

    // 4. Smart Bin Markers
    bins.forEach(b => {
      let bg = '#10b981'; // green
      let border = '#059669';
      let shadow = 'rgba(16,185,129,0.4)';

      if (b.sensor_health === 'TILTED') {
        bg = '#a855f7';
        border = '#7e22ce';
        shadow = 'rgba(168,85,247,0.5)';
      } else if (b.current_fill_pct >= 85.0) {
        bg = '#f43f5e';
        border = '#e11d48';
        shadow = 'rgba(244,63,94,0.6)';
      } else if (b.current_fill_pct >= 70.0) {
        bg = '#f59e0b';
        border = '#d97706';
        shadow = 'rgba(245,158,11,0.5)';
      }

      const binIcon = L.divIcon({
        className: 'custom-bin-marker',
        html: `
          <div style="background:${bg}; border:2px solid ${border}; color:#ffffff; border-radius:9999px; width:26px; height:26px; display:flex; align-items:center; justify-content:center; box-shadow:0 0 10px ${shadow}; font-size:10px; font-weight:bold;">
            ${Math.round(b.current_fill_pct)}%
          </div>
        `,
        iconSize: [26, 26],
        iconAnchor: [13, 13],
      });

      const popupHtml = `
        <div class="p-2.5 text-xs text-slate-100 min-w-[210px]">
          <div class="flex items-center justify-between border-b border-slate-700/60 pb-1.5 mb-2">
            <div>
              <span class="font-bold text-white text-sm">${b.name}</span>
              <div class="text-[10px] text-slate-400">${b.id} • ${b.zone}</div>
            </div>
            <span class="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${
              b.waste_type === 'RECYCLABLE' ? 'bg-emerald-500/20 text-emerald-300' :
              b.waste_type === 'ORGANIC' ? 'bg-amber-500/20 text-amber-300' :
              b.waste_type === 'HAZARDOUS' ? 'bg-purple-500/20 text-purple-300' : 'bg-sky-500/20 text-sky-300'
            }">${b.waste_type}</span>
          </div>

          <div class="space-y-1 mb-2.5">
            <div class="flex justify-between">
              <span class="text-slate-400">Fill Level:</span>
              <span class="font-bold ${b.current_fill_pct >= 85 ? 'text-rose-400' : b.current_fill_pct >= 70 ? 'text-amber-400' : 'text-emerald-400'}">${b.current_fill_pct.toFixed(1)}%</span>
            </div>
            <div class="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
              <div class="h-full rounded-full ${b.current_fill_pct >= 85 ? 'bg-rose-500' : b.current_fill_pct >= 70 ? 'bg-amber-500' : 'bg-emerald-500'}" style="width: ${b.current_fill_pct}%"></div>
            </div>

            <div class="flex justify-between pt-1">
              <span class="text-slate-400">Weight Payload:</span>
              <span class="font-medium text-slate-200">${b.current_weight_kg.toFixed(1)} kg</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">Time to Overflow:</span>
              <span class="font-bold text-amber-300">${b.hours_to_overflow.toFixed(1)} hrs</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">Collection Priority:</span>
              <span class="font-bold text-cyan-400">${b.collection_priority.toFixed(1)} / 100</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">Sensor Status:</span>
              <span class="font-medium ${b.sensor_health === 'OK' ? 'text-emerald-400' : 'text-purple-400'}">${b.sensor_health}</span>
            </div>
          </div>
        </div>
      `;

      L.marker([b.latitude, b.longitude], { icon: binIcon })
        .bindPopup(popupHtml)
        .addTo(layers);
    });

  }, [bins, vehicles, plan]);

  return (
    <div className="relative w-full h-[540px] rounded-2xl overflow-hidden border border-slate-800 shadow-xl bg-slate-950">
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Map Overlay Controls / Legend */}
      <div className="absolute top-4 right-4 z-[1000] bg-slate-900/90 border border-slate-800 rounded-xl p-3 shadow-lg backdrop-blur-md text-xs space-y-2 pointer-events-auto">
        <div className="font-semibold text-slate-200 text-[11px] uppercase tracking-wider mb-1 flex items-center justify-between">
          <span>GIS Layers</span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-rose-500"></span>
          <span className="text-slate-300">Critical (&gt;85% Fill)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-amber-500"></span>
          <span className="text-slate-300">Warning (70-85%)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
          <span className="text-slate-300">Normal (&lt;70%)</span>
        </div>
        <div className="border-t border-slate-800 pt-1.5 space-y-1">
          <div className="text-[10px] text-slate-400 font-semibold uppercase">CVRP Active Paths:</div>
          <div className="flex items-center gap-2 text-[11px] text-sky-400">
            <span className="w-4 h-0.5 bg-sky-400"></span> General Stream
          </div>
          <div className="flex items-center gap-2 text-[11px] text-emerald-400">
            <span className="w-4 h-0.5 bg-emerald-400"></span> Recyclables Stream
          </div>
          <div className="flex items-center gap-2 text-[11px] text-amber-400">
            <span className="w-4 h-0.5 bg-amber-400"></span> Organics Stream
          </div>
        </div>
      </div>
    </div>
  );
};
