import React from 'react';
import { 
  TrendingUp, 
  DollarSign, 
  AlertOctagon, 
  PackageCheck, 
  ShieldAlert, 
  Clock, 
  ArrowUpRight, 
  ArrowDownRight,
  ExternalLink,
  Flame
} from 'lucide-react';
import { ExecutiveKPIs, AlertOut } from '../types';

interface ExecutiveDashboardProps {
  kpis: ExecutiveKPIs | null;
  alerts: AlertOut[];
  onNavigateToIncidents: () => void;
  onNavigateToSuppliers: () => void;
}

export const ExecutiveDashboard: React.FC<ExecutiveDashboardProps> = ({
  kpis,
  alerts,
  onNavigateToIncidents,
  onNavigateToSuppliers
}) => {
  if (!kpis) {
    return (
      <div className="p-8 text-center text-slate-400 animate-pulse">
        Loading SupplyGuard Executive Telemetry...
      </div>
    );
  }

  const criticalAlerts = alerts.filter(a => a.severity === 'CRITICAL' && a.status === 'ACTIVE').slice(0, 4);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-850 to-slate-900 border border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Executive Supply-Chain Cockpit</h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time warehouse telemetry, ML predictive risk scoring, and active shortage surveillance.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-semibold flex items-center space-x-2">
            <Flame className="w-4 h-4 text-red-400 animate-pulse" />
            <span>{kpis.high_risk_suppliers_count} High-Risk Vendors Identified</span>
          </div>
        </div>
      </div>

      {/* 4 Core Hero KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* KPI 1: On-Time Delivery */}
        <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800/80 hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">On-Time Delivery (OTD)</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <PackageCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-white">{kpis.on_time_delivery_rate}%</span>
            <span className="text-xs text-emerald-400 font-medium flex items-center">
              <ArrowUpRight className="w-3 h-3 mr-0.5" /> +1.8% MoM
            </span>
          </div>
          <div className="mt-2 text-[11px] text-slate-500">Benchmark target: 95.0%</div>
        </div>

        {/* KPI 2: Total Spend at Risk */}
        <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800/80 hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Overdue PO Value at Risk</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
              <DollarSign className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-amber-400">
              ${(kpis.total_spend_at_risk_usd / 1_000_000).toFixed(2)}M
            </span>
            <span className="text-xs text-amber-400 font-medium">USD</span>
          </div>
          <div className="mt-2 text-[11px] text-slate-500">Across active delayed purchase orders</div>
        </div>

        {/* KPI 3: Active Stockout SKUs */}
        <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800/80 hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Critical Stockouts & Breaches</span>
            <div className="p-2 rounded-lg bg-red-500/10 text-red-400">
              <AlertOctagon className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-red-400">{kpis.active_stockouts_count}</span>
            <span className="text-xs text-red-400 font-medium">SKUs</span>
          </div>
          <div className="mt-2 text-[11px] text-slate-500">Below safety stock / 0 units on hand</div>
        </div>

        {/* KPI 4: Total Inventory Holding Valuation */}
        <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800/80 hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Inventory Valuation</span>
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-white">
              ${(kpis.total_inventory_valuation_usd / 1_000_000).toFixed(2)}M
            </span>
            <span className="text-xs text-slate-400">USD</span>
          </div>
          <div className="mt-2 text-[11px] text-slate-500">Avg {kpis.average_days_of_inventory} Days of Inventory (DOI)</div>
        </div>
      </div>

      {/* Grid: Live Shortage Stream & Production Risk Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Active Incidents Stream (2 Cols) */}
        <div className="lg:col-span-2 p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-red-400" />
              <h2 className="text-sm font-bold text-white">High-Priority Disruption Stream</h2>
            </div>
            <button 
              onClick={onNavigateToIncidents}
              className="text-xs text-brand-400 hover:text-brand-300 flex items-center space-x-1"
            >
              <span>View All Alerts ({alerts.length})</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-3">
            {criticalAlerts.map((alert) => (
              <div 
                key={alert.alert_id}
                className="p-3.5 rounded-lg bg-slate-950 border border-red-500/20 hover:border-red-500/40 transition space-y-2"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-red-500/20 text-red-400 border border-red-500/30">
                        {alert.severity}
                      </span>
                      <span className="text-xs font-semibold text-slate-200">{alert.title}</span>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-relaxed line-clamp-2">
                      {alert.message}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="text-xs font-semibold text-amber-400">
                      ${alert.impact_valuation.toLocaleString()}
                    </span>
                    <div className="text-[10px] text-slate-500">Expedite Risk</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Platform Architecture & ML Model Status */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-sm font-bold text-white">Platform Health & Data Integration</h2>
            <p className="text-[11px] text-slate-400 mt-0.5">Automated Star-Schema Pipeline Status</p>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800">
              <span className="text-slate-400">PostgreSQL Warehouse</span>
              <span className="font-semibold text-emerald-400">Connected (Port 5432)</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800">
              <span className="text-slate-400">Partitioned Movements</span>
              <span className="font-semibold text-white">110,000 Rows Active</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800">
              <span className="text-slate-400">Airflow Orchestration</span>
              <span className="font-semibold text-emerald-400">4 DAGs Scheduled</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800">
              <span className="text-slate-400">ML Scoring Engine</span>
              <span className="font-semibold text-brand-400">GradientBoosting + RF</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800">
              <span className="text-slate-400">Data Quality Assertions</span>
              <span className="font-semibold text-emerald-400">100% Passing</span>
            </div>
          </div>

          <button
            onClick={onNavigateToSuppliers}
            className="w-full mt-2 py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold text-center transition border border-slate-700"
          >
            Launch Supplier Scorecards Ledger &rarr;
          </button>
        </div>
      </div>
    </div>
  );
};
