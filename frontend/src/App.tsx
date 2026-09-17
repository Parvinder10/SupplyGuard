import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar, TabType } from './components/Sidebar';
import { ExecutiveDashboard } from './components/ExecutiveDashboard';
import { SupplierScorecards } from './components/SupplierScorecards';
import { InventoryRadar } from './components/InventoryRadar';
import { PurchaseOrders } from './components/PurchaseOrders';
import { IncidentManagement } from './components/IncidentManagement';
import { ETLGovernance } from './components/ETLGovernance';

import { api } from './services/api';
import { 
  ExecutiveKPIs, 
  SupplierScorecard, 
  MaterialOut, 
  PurchaseOrderOut, 
  AlertOut, 
  CorrectiveActionOut,
  ETLAuditLogOut,
  ETLRejectedRecordOut,
  DataQualityTestOut,
  CorrectiveActionCreate
} from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<TabType>('dashboard');
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Core Data Stores
  const [kpis, setKpis] = useState<ExecutiveKPIs | null>(null);
  const [suppliers, setSuppliers] = useState<SupplierScorecard[]>([]);
  const [materials, setMaterials] = useState<MaterialOut[]>([]);
  const [orders, setOrders] = useState<PurchaseOrderOut[]>([]);
  const [alerts, setAlerts] = useState<AlertOut[]>([]);
  const [correctiveActions, setCorrectiveActions] = useState<CorrectiveActionOut[]>([]);
  const [auditLogs, setAuditLogs] = useState<ETLAuditLogOut[]>([]);
  const [rejectedRecords, setRejectedRecords] = useState<ETLRejectedRecordOut[]>([]);
  const [dqResults, setDqResults] = useState<DataQualityTestOut[]>([]);

  const loadAllData = async () => {
    try {
      const [
        kpiData,
        supData,
        matData,
        poData,
        alertData,
        actionData,
        auditData,
        rejectData,
        dqData
      ] = await Promise.all([
        api.getKPIs(),
        api.getSuppliers(),
        api.getMaterials(),
        api.getPurchaseOrders(),
        api.getAlerts(),
        api.getCorrectiveActions(),
        api.getETLAuditLogs(),
        api.getETLRejectedRecords(),
        api.getDataQualityResults()
      ]);

      setKpis(kpiData);
      setSuppliers(supData);
      setMaterials(matData);
      setOrders(poData);
      setAlerts(alertData);
      setCorrectiveActions(actionData);
      setAuditLogs(auditData);
      setRejectedRecords(rejectData);
      setDqResults(dqData);
    } catch (err) {
      console.error('Failed to load portal data from backend:', err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handleRefreshModels = async () => {
    setIsRefreshing(true);
    try {
      await api.triggerRiskScoring();
      await loadAllData();
    } catch (e) {
      console.error('Risk rescoring failed:', e);
      setIsRefreshing(false);
    }
  };

  const handleUpdateAlert = async (alertId: string, status: string) => {
    try {
      const updated = await api.updateAlertStatus(alertId, status);
      setAlerts(prev => prev.map(a => a.alert_id === alertId ? updated : a));
      // Refresh KPIs count
      const updatedKpis = await api.getKPIs();
      setKpis(updatedKpis);
    } catch (err) {
      console.error('Failed to update alert:', err);
    }
  };

  const handleCreateAction = async (payload: CorrectiveActionCreate) => {
    try {
      const newAction = await api.createCorrectiveAction(payload);
      setCorrectiveActions(prev => [newAction, ...prev]);
      const updatedKpis = await api.getKPIs();
      setKpis(updatedKpis);
    } catch (err) {
      console.error('Failed to create action:', err);
    }
  };

  const handleUpdateAction = async (actionId: string, payload: Partial<CorrectiveActionOut>) => {
    try {
      const updated = await api.updateCorrectiveAction(actionId, payload);
      setCorrectiveActions(prev => prev.map(a => a.action_id === actionId ? updated : a));
      const updatedKpis = await api.getKPIs();
      setKpis(updatedKpis);
    } catch (err) {
      console.error('Failed to update action:', err);
    }
  };

  const handleMitigateSupplier = (supplier: SupplierScorecard) => {
    setCurrentTab('incidents');
  };

  const activeAlertsCount = alerts.filter(a => a.status === 'ACTIVE').length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar 
        activeAlertsCount={activeAlertsCount}
        onRefresh={handleRefreshModels}
        isRefreshing={isRefreshing}
      />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar 
          currentTab={currentTab}
          onSelectTab={setCurrentTab}
          activeAlertsCount={activeAlertsCount}
        />

        <main className="flex-1 overflow-y-auto p-6 lg:p-8">
          {isLoading ? (
            <div className="h-96 flex flex-col items-center justify-center space-y-4">
              <div className="w-10 h-10 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-xs text-slate-400 font-mono">
                Connecting to SupplyGuard Data Warehouse & Risk Services...
              </p>
            </div>
          ) : (
            <>
              {currentTab === 'dashboard' && (
                <ExecutiveDashboard
                  kpis={kpis}
                  alerts={alerts}
                  onNavigateToIncidents={() => setCurrentTab('incidents')}
                  onNavigateToSuppliers={() => setCurrentTab('suppliers')}
                />
              )}

              {currentTab === 'suppliers' && (
                <SupplierScorecards
                  suppliers={suppliers}
                  onMitigateSupplier={handleMitigateSupplier}
                />
              )}

              {currentTab === 'inventory' && (
                <InventoryRadar
                  materials={materials}
                />
              )}

              {currentTab === 'orders' && (
                <PurchaseOrders
                  orders={orders}
                />
              )}

              {currentTab === 'incidents' && (
                <IncidentManagement
                  alerts={alerts}
                  correctiveActions={correctiveActions}
                  onUpdateAlert={handleUpdateAlert}
                  onCreateAction={handleCreateAction}
                  onUpdateAction={handleUpdateAction}
                />
              )}

              {currentTab === 'etl' && (
                <ETLGovernance
                  auditLogs={auditLogs}
                  rejectedRecords={rejectedRecords}
                  dqResults={dqResults}
                />
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
};
export default App;
