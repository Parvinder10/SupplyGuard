import React, { useState } from 'react';
import { Search, Filter, ShieldAlert, ArrowUpDown, ChevronRight, Eye } from 'lucide-react';
import { SupplierScorecard } from '../types';
import { SupplierDetailModal } from './SupplierDetailModal';

interface SupplierScorecardsProps {
  suppliers: SupplierScorecard[];
  onMitigateSupplier: (supplier: SupplierScorecard) => void;
}

export const SupplierScorecards: React.FC<SupplierScorecardsProps> = ({ suppliers, onMitigateSupplier }) => {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedRiskTier, setSelectedRiskTier] = useState<string>('ALL');
  const [selectedSupplier, setSelectedSupplier] = useState<SupplierScorecard | null>(null);

  // Categories
  const categories = ['ALL', ...Array.from(new Set(suppliers.map(s => s.category)))];
  const riskTiers = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

  const filtered = suppliers.filter(s => {
    const matchesSearch = search === '' || 
      s.name.toLowerCase().includes(search.toLowerCase()) || 
      s.code.toLowerCase().includes(search.toLowerCase()) ||
      s.country.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = selectedCategory === 'ALL' || s.category === selectedCategory;
    const matchesRisk = selectedRiskTier === 'ALL' || s.risk_tier === selectedRiskTier;
    return matchesSearch && matchesCategory && matchesRisk;
  });

  const getTierBadge = (tier: string) => {
    switch (tier) {
      case 'CRITICAL': return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'HIGH': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'MEDIUM': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      default: return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Supplier 360 Scorecards & Risk Matrix</h1>
          <p className="text-xs text-slate-400 mt-1">
            Evaluating {suppliers.length} active enterprise vendors across OTD %, defect PPM, and ML disruption scores.
          </p>
        </div>
      </div>

      {/* Filter Controls */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search vendor name, code, or country..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500"
          />
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400 font-medium">Category:</span>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-brand-500"
          >
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400 font-medium">Risk Tier:</span>
          <select
            value={selectedRiskTier}
            onChange={(e) => setSelectedRiskTier(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-brand-500"
          >
            {riskTiers.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
      </div>

      {/* Suppliers Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-medium uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Supplier & Code</th>
                <th className="py-3 px-4">Category & Origin</th>
                <th className="py-3 px-4">Tier</th>
                <th className="py-3 px-4 text-center">OTD %</th>
                <th className="py-3 px-4 text-center">Defect PPM</th>
                <th className="py-3 px-4 text-center">Avg Variance</th>
                <th className="py-3 px-4 text-center">ML Risk Score</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filtered.map((s) => (
                <tr 
                  key={s.supplier_id} 
                  className="hover:bg-slate-800/40 transition cursor-pointer"
                  onClick={() => setSelectedSupplier(s)}
                >
                  <td className="py-3 px-4 font-semibold text-white">
                    <div>{s.name}</div>
                    <div className="text-[10px] text-slate-500 font-mono">{s.code}</div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="text-slate-200">{s.category}</div>
                    <div className="text-[10px] text-slate-400">{s.city}, {s.country}</div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300">
                      {s.tier}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center font-semibold">
                    <span className={s.otd_percentage < 85 ? 'text-red-400' : 'text-emerald-400'}>
                      {s.otd_percentage}%
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center font-mono">
                    <span className={s.overall_defect_ppm > 5000 ? 'text-red-400' : 'text-slate-300'}>
                      {s.overall_defect_ppm.toLocaleString()}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center font-mono">
                    <span className={s.avg_lead_time_variance_days > 5 ? 'text-amber-400' : 'text-slate-400'}>
                      +{s.avg_lead_time_variance_days}d
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className={`px-2.5 py-1 rounded-md text-[11px] font-bold border ${getTierBadge(s.risk_tier)}`}>
                      {s.risk_score} / 100
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedSupplier(s);
                      }}
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-brand-400 hover:text-brand-300 transition"
                      title="Inspect Risk Attribution"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal */}
      {selectedSupplier && (
        <SupplierDetailModal
          supplier={selectedSupplier}
          onClose={() => setSelectedSupplier(null)}
          onMitigate={(sup) => {
            setSelectedSupplier(null);
            onMitigateSupplier(sup);
          }}
        />
      )}
    </div>
  );
};
