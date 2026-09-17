import React from 'react';
import { 
  LayoutDashboard, 
  Users, 
  Boxes, 
  ShoppingCart, 
  AlertTriangle, 
  GitBranch,
  BarChart3,
  CheckSquare
} from 'lucide-react';

export type TabType = 
  | 'dashboard' 
  | 'suppliers' 
  | 'inventory' 
  | 'orders' 
  | 'incidents' 
  | 'etl';

interface SidebarProps {
  currentTab: TabType;
  onSelectTab: (tab: TabType) => void;
  activeAlertsCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab, activeAlertsCount }) => {
  const menuItems = [
    { id: 'dashboard', label: 'Executive Cockpit', icon: LayoutDashboard },
    { id: 'suppliers', label: 'Supplier 360 & Risk', icon: Users },
    { id: 'inventory', label: 'Inventory & Stockouts', icon: Boxes },
    { id: 'orders', label: 'Purchase Order Delays', icon: ShoppingCart },
    { 
      id: 'incidents', 
      label: 'Incident & Corrective Actions', 
      icon: AlertTriangle,
      badge: activeAlertsCount > 0 ? activeAlertsCount : undefined 
    },
    { id: 'etl', label: 'ETL Governance & DQ', icon: GitBranch },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/40 p-4 flex flex-col justify-between shrink-0">
      <div className="space-y-6">
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider px-3">
          Core Navigation
        </div>
        <nav className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id as TabType)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? 'bg-brand-500/10 text-brand-400 border border-brand-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-brand-400' : 'text-slate-500'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge !== undefined && (
                  <span className="px-2 py-0.5 text-xs font-bold bg-red-500/20 text-red-400 border border-red-500/30 rounded-full">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Analytics Reference Card */}
      <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs space-y-2">
        <div className="flex items-center justify-between text-slate-400 font-semibold">
          <span>Apache Superset 3.0</span>
          <span className="w-2 h-2 rounded-full bg-blue-500" />
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          6 Enterprise dashboards provisioned at port 8088. Native cross-filtering enabled.
        </p>
        <a 
          href="http://localhost:8088" 
          target="_blank" 
          rel="noreferrer"
          className="text-brand-400 hover:underline flex items-center space-x-1 text-[11px] font-medium"
        >
          <span>Open Superset Portal</span>
          <span>&rarr;</span>
        </a>
      </div>
    </aside>
  );
};
