import React, { useState } from 'react';
import { Search, AlertCircle, AlertTriangle, CheckCircle, Package, ShieldAlert } from 'lucide-react';
import { MaterialOut } from '../types';

interface InventoryRadarProps {
  materials: MaterialOut[];
}

export const InventoryRadar: React.FC<InventoryRadarProps> = ({ materials }) => {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [criticalOnly, setCriticalOnly] = useState(false);

  const categories = ['ALL', ...Array.from(new Set(materials.map(m => m.category)))];

  const filtered = materials.filter(m => {
    const matchesSearch = search === '' ||
      m.name.toLowerCase().includes(search.toLowerCase()) ||
      m.sku.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = selectedCategory === 'ALL' || m.category === selectedCategory;
    const matchesCritical = !criticalOnly || m.is_critical;
    return matchesSearch && matchesCategory && matchesCritical;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'STOCKOUT':
        return 'bg-red-500/20 text-red-400 border-red-500/40';
      case 'SAFETY_STOCK_BREACH':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      case 'REORDER_TRIGGER':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40';
      default:
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Inventory Intelligence & Stockout Radar</h1>
        <p className="text-xs text-slate-400 mt-1">
          Surveillance across {materials.length} production SKUs, monitoring safety stock thresholds and Days of Inventory (DOI).
        </p>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search material SKU, name..."
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

        <label className="flex items-center space-x-2 cursor-pointer text-xs text-slate-300 select-none">
          <input
            type="checkbox"
            checked={criticalOnly}
            onChange={(e) => setCriticalOnly(e.target.checked)}
            className="rounded border-slate-700 bg-slate-950 text-brand-500 focus:ring-0"
          />
          <span className="font-semibold text-brand-400">Critical BOM SKUs Only</span>
        </label>
      </div>

      {/* Materials Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-medium uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">SKU & Material Name</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4 text-center">Critical</th>
                <th className="py-3 px-4 text-center">Current Stock</th>
                <th className="py-3 px-4 text-center">Safety Stock</th>
                <th className="py-3 px-4 text-center">Days of Inv (DOI)</th>
                <th className="py-3 px-4 text-center">Health Status</th>
                <th className="py-3 px-4 text-center">Stockout Risk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filtered.map((m) => (
                <tr key={m.material_id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-4">
                    <div className="font-semibold text-white">{m.name}</div>
                    <div className="text-[10px] font-mono text-slate-500">{m.sku}</div>
                  </td>
                  <td className="py-3 px-4 text-slate-300">{m.category}</td>
                  <td className="py-3 px-4 text-center">
                    {m.is_critical ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/20 text-red-400 border border-red-500/30">
                        CRITICAL
                      </span>
                    ) : (
                      <span className="text-slate-600">-</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-center font-mono font-bold text-white">
                    {m.current_stock.toLocaleString()} {m.unit_of_measure}
                  </td>
                  <td className="py-3 px-4 text-center font-mono text-slate-400">
                    {m.safety_stock_level.toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-center font-mono font-semibold">
                    <span className={m.days_of_inventory < 10 ? 'text-red-400' : 'text-emerald-400'}>
                      {m.days_of_inventory} Days
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getStatusBadge(m.stock_health_status)}`}>
                      {m.stock_health_status.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center font-semibold">
                    <span className={m.stockout_risk_score > 60 ? 'text-red-400' : 'text-slate-300'}>
                      {m.stockout_risk_score} / 100
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
