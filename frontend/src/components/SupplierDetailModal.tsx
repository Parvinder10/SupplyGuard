import React from 'react';
import { X, ShieldAlert, AlertTriangle, CheckCircle, Info, ExternalLink, Activity } from 'lucide-react';
import { SupplierScorecard } from '../types';

interface SupplierDetailModalProps {
  supplier: SupplierScorecard | null;
  onClose: () => void;
  onMitigate: (supplier: SupplierScorecard) => void;
}

export const SupplierDetailModal: React.FC<SupplierDetailModalProps> = ({
  supplier,
  onClose,
  onMitigate
}) => {
  if (!supplier) return null;

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'CRITICAL': return 'bg-red-500/20 text-red-400 border-red-500/40';
      case 'HIGH': return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      case 'MEDIUM': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40';
      default: return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl p-6 space-y-6 animate-in fade-in zoom-in duration-150">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center space-x-3">
              <span className={`px-2.5 py-1 rounded-md text-xs font-bold border ${getTierColor(supplier.risk_tier)}`}>
                {supplier.risk_tier} RISK
              </span>
              <span className="text-xs font-mono text-slate-400">{supplier.code}</span>
              <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300">{supplier.tier}</span>
            </div>
            <h2 className="text-lg font-bold text-white mt-1">{supplier.name}</h2>
            <p className="text-xs text-slate-400">{supplier.city}, {supplier.country} • {supplier.category}</p>
          </div>
          <button 
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Explainable AI Narrative Card */}
        <div className="p-4 rounded-xl bg-slate-950 border border-brand-500/30 space-y-2">
          <div className="flex items-center space-x-2 text-brand-400">
            <Activity className="w-4 h-4" />
            <span className="text-xs font-bold uppercase tracking-wider">Explainable AI Narrative & Root Drivers</span>
          </div>
          <p className="text-xs text-slate-200 leading-relaxed font-sans">
            {supplier.explanation_text}
          </p>
        </div>

        {/* Feature Contribution Breakdown */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Machine Learning Feature Attribution (% Contribution to Score)
          </h3>
          <div className="space-y-2">
            {supplier.top_contributing_factors.map((factor, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-300 capitalize font-medium">
                    {factor.feature.replace(/_/g, ' ')}
                  </span>
                  <span className="text-brand-400 font-semibold">{factor.impact_percentage}%</span>
                </div>
                <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-brand-600 to-emerald-400 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, factor.impact_percentage)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Key Operational Scorecard Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase">On-Time Delivery</span>
            <div className="text-base font-bold text-white mt-0.5">{supplier.otd_percentage}%</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase">Defect Rate</span>
            <div className="text-base font-bold text-white mt-0.5">{supplier.overall_defect_ppm.toLocaleString()} PPM</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase">Avg Variance</span>
            <div className="text-base font-bold text-amber-400 mt-0.5">+{supplier.avg_lead_time_variance_days} Days</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase">Total Spend</span>
            <div className="text-base font-bold text-white mt-0.5">${(supplier.total_spend / 1000).toFixed(0)}k</div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
          >
            Close
          </button>
          <button
            onClick={() => onMitigate(supplier)}
            className="px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-lg shadow-brand-600/20"
          >
            Initiate Corrective Action Plan
          </button>
        </div>
      </div>
    </div>
  );
};
