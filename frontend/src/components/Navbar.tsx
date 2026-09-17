import React from 'react';
import { ShieldAlert, Bell, Database, Activity, RefreshCw, UserCheck } from 'lucide-react';

interface NavbarProps {
  activeAlertsCount: number;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ activeAlertsCount, onRefresh, isRefreshing }) => {
  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center space-x-3">
        <div className="p-2 bg-brand-500/10 border border-brand-500/30 rounded-lg text-brand-500 flex items-center justify-center shadow-lg shadow-brand-500/5">
          <ShieldAlert className="w-6 h-6 text-brand-500" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-lg text-white tracking-tight">SUPPLY<span className="text-brand-500">GUARD</span></span>
            <span className="text-xs uppercase px-1.5 py-0.5 rounded bg-brand-500/20 text-brand-400 font-semibold tracking-wider">Enterprise DI</span>
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">Manufacturing Supply-Chain & Inventory Risk Platform</p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-brand-500' : ''}`} />
          <span>{isRefreshing ? 'Scoring...' : 'Sync Models'}</span>
        </button>

        <div className="flex items-center space-x-2 px-3 py-1 bg-slate-800/60 rounded-full border border-slate-700/60 text-xs text-slate-300">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Warehouse Connected (Postgres Star-Schema)</span>
        </div>

        <div className="relative">
          <div className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white cursor-pointer relative">
            <Bell className="w-4 h-4" />
            {activeAlertsCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full text-[10px] font-bold flex items-center justify-center">
                {activeAlertsCount > 9 ? '9+' : activeAlertsCount}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2 pl-3 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-brand-600 to-emerald-400 flex items-center justify-center text-slate-950 font-bold text-xs">
            DI
          </div>
          <div className="hidden md:block text-left">
            <div className="text-xs font-semibold text-slate-200">Senior DI Lead</div>
            <div className="text-[10px] text-slate-400">admin@supplyguard</div>
          </div>
        </div>
      </div>
    </header>
  );
};
