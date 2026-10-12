import React, { useState } from 'react';
import { CVAnalysisResult } from '../types';
import { api } from '../services/api';
import { Eye, ShieldAlert, CheckCircle, Sparkles, AlertTriangle } from 'lucide-react';

interface RecyclingCVInspectorProps {
  binId?: string;
}

export const RecyclingCVInspector: React.FC<RecyclingCVInspectorProps> = ({ binId = 'BIN-005' }) => {
  const [sampleType, setSampleType] = useState('clean_recyclables');
  const [result, setResult] = useState<CVAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const runAnalysis = async () => {
    setIsAnalyzing(true);
    try {
      const data = await api.analyzeCV(binId, sampleType);
      setResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center space-x-2">
          <Eye className="w-5 h-5 text-teal-400" />
          <h2 className="text-base font-bold text-white tracking-tight">AI Computer Vision Recycling & Contamination Inspector</h2>
        </div>
        <span className="text-[11px] font-mono text-teal-400 bg-teal-500/10 px-2 py-0.5 rounded border border-teal-500/20">
          YOLOv8-WasteSeg Active
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Input & Control Panel */}
        <div className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Select Inspection Telemetry Sample:</label>
            <select
              value={sampleType}
              onChange={e => setSampleType(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-teal-500"
            >
              <option value="clean_recyclables">Sample A: High-Purity Dry Recyclables (PET/Cardboard)</option>
              <option value="contaminated_plastics">Sample B: Severe Contamination (Lithium Battery & Grease)</option>
              <option value="organic_compost">Sample C: Food Scrap & Composting Stream</option>
              <option value="general_municipal">Sample D: Mixed Municipal Residuals</option>
            </select>
          </div>

          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs text-slate-400 space-y-1.5">
            <div className="flex justify-between">
              <span>Target Bin ID:</span>
              <span className="font-mono text-white">{binId}</span>
            </div>
            <div className="flex justify-between">
              <span>Sensor Camera:</span>
              <span className="text-emerald-400">Wide-Angle Overhead RGB-D</span>
            </div>
            <div className="flex justify-between">
              <span>Inference Engine:</span>
              <span className="text-slate-300">TensorRT FP16 Edge Optimizer</span>
            </div>
          </div>

          <button
            onClick={runAnalysis}
            disabled={isAnalyzing}
            className="w-full py-2.5 bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold rounded-xl text-xs flex items-center justify-center gap-2 transition active:scale-95 disabled:opacity-50"
          >
            <Sparkles className={`w-4 h-4 ${isAnalyzing ? 'animate-spin' : ''}`} />
            {isAnalyzing ? 'Running Vision Inference...' : 'Perform AI Optical Inspection'}
          </button>
        </div>

        {/* Results Screen */}
        <div className="lg:col-span-2 bg-slate-950 rounded-xl border border-slate-800 p-4">
          {!result ? (
            <div className="h-48 flex flex-col items-center justify-center text-slate-500 text-xs text-center space-y-2">
              <Eye className="w-8 h-8 text-slate-700 animate-pulse" />
              <span>Click "Perform AI Optical Inspection" to evaluate waste stream purity and contamination.</span>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Top Banner */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                <div className="flex items-center gap-2">
                  {result.is_contaminated ? (
                    <ShieldAlert className="w-5 h-5 text-rose-400" />
                  ) : (
                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                  )}
                  <div>
                    <div className="font-bold text-xs text-white">
                      {result.is_contaminated ? 'Contamination Threshold Exceeded' : 'Stream Certified Clean'}
                    </div>
                    <div className="text-[11px] text-slate-400">Stream: {result.waste_type}</div>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-xs font-mono">
                  <div>
                    <span className="text-slate-400">Purity: </span>
                    <span className="font-bold text-emerald-400">{result.purity_score_pct}%</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Contamination: </span>
                    <span className={`font-bold ${result.is_contaminated ? 'text-rose-400' : 'text-slate-300'}`}>
                      {result.contamination_pct}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Detected Objects Table */}
              <div>
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Detected Items & Material Segregation ({result.detected_items.length})
                </div>
                <div className="space-y-1.5">
                  {result.detected_items.map((item, idx) => (
                    <div
                      key={idx}
                      className={`p-2 rounded-lg border text-xs flex items-center justify-between ${
                        item.is_contaminant
                          ? 'bg-rose-950/30 border-rose-900/50 text-rose-300'
                          : 'bg-slate-900/50 border-slate-800/80 text-slate-200'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {item.is_contaminant ? (
                          <AlertTriangle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                        ) : (
                          <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        )}
                        <div>
                          <div className="font-medium">{item.label}</div>
                          <div className="text-[10px] text-slate-400">{item.category}</div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 text-right">
                        <span className="text-[10px] text-slate-400 font-mono">
                          {(item.confidence * 100).toFixed(0)}% conf
                        </span>
                        <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${
                          item.is_contaminant ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'
                        }`}>
                          {item.is_contaminant ? 'Contaminant' : 'Valid'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recommendation Callout */}
              <div className="p-3 bg-slate-900 rounded-xl border border-slate-800 text-xs text-slate-300">
                <span className="font-semibold text-teal-400">Operational Routing Directive: </span>
                {result.recommendation}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
