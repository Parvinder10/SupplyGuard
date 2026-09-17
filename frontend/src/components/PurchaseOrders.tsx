import React, { useState } from 'react';
import { Search, ShoppingCart, Clock, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { PurchaseOrderOut } from '../types';

interface PurchaseOrdersProps {
  orders: PurchaseOrderOut[];
}

export const PurchaseOrders: React.FC<PurchaseOrdersProps> = ({ orders }) => {
  const [search, setSearch] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('ALL');

  const statuses = ['ALL', 'OVERDUE', 'IN_TRANSIT', 'DELIVERED', 'PENDING'];

  const filtered = orders.filter(po => {
    const matchesSearch = search === '' || 
      po.po_number.toLowerCase().includes(search.toLowerCase()) ||
      po.supplier_name.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = selectedStatus === 'ALL' || po.status === selectedStatus;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OVERDUE':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'IN_TRANSIT':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'DELIVERED':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'CANCELLED':
        return 'bg-slate-700 text-slate-400 border-slate-600';
      default:
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Purchase Order Delays & Procurement Velocity</h1>
        <p className="text-xs text-slate-400 mt-1">
          Tracking purchase orders across global supplier networks with automated delivery delay calculations.
        </p>
      </div>

      {/* Filter bar */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search PO number or vendor..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500"
          />
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400 font-medium">Status:</span>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-brand-500"
          >
            {statuses.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>

      {/* PO Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-medium uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">PO Number</th>
                <th className="py-3 px-4">Supplier</th>
                <th className="py-3 px-4">Order Date</th>
                <th className="py-3 px-4">Promised Date</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-center">Days Overdue</th>
                <th className="py-3 px-4 text-right">Order Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filtered.map((po) => (
                <tr key={po.po_id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-4 font-mono font-semibold text-white">
                    {po.po_number}
                  </td>
                  <td className="py-3 px-4 font-medium text-slate-200">
                    {po.supplier_name || po.supplier_id}
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-400">{po.order_date}</td>
                  <td className="py-3 px-4 font-mono text-slate-400">{po.promised_delivery_date}</td>
                  <td className="py-3 px-4 text-center">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getStatusBadge(po.status)}`}>
                      {po.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center font-mono font-semibold">
                    {po.days_overdue > 0 ? (
                      <span className="text-red-400">+{po.days_overdue} Days</span>
                    ) : (
                      <span className="text-slate-600">-</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-bold text-white">
                    ${po.total_amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
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
