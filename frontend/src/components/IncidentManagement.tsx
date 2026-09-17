import React, { useState } from 'react';
import { 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  UserPlus, 
  ShieldAlert, 
  CheckSquare, 
  FileText, 
  Plus,
  ArrowRight,
  Filter
} from 'lucide-react';
import { AlertOut, CorrectiveActionOut, CorrectiveActionCreate } from '../types';

interface IncidentManagementProps {
  alerts: AlertOut[];
  correctiveActions: CorrectiveActionOut[];
  onUpdateAlert: (alertId: string, status: string) => void;
  onCreateAction: (payload: CorrectiveActionCreate) => void;
  onUpdateAction: (actionId: string, payload: Partial<CorrectiveActionOut>) => void;
}

export const IncidentManagement: React.FC<IncidentManagementProps> = ({
  alerts,
  correctiveActions,
  onUpdateAlert,
  onCreateAction,
  onUpdateAction
}) => {
  const [selectedSeverity, setSelectedSeverity] = useState('ALL');
  const [selectedAlertStatus, setSelectedAlertStatus] = useState('ACTIVE');
  const [activeTab, setActiveTab] = useState<'alerts' | 'actions'>('alerts');

  // Modal State for Creating Corrective Action
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<AlertOut | null>(null);
  const [actionTitle, setActionTitle] = useState('');
  const [actionDescription, setActionDescription] = useState('');
  const [assignedTo, setAssignedTo] = useState('Lead Strategic Procurement Manager');
  const [priority, setPriority] = useState('HIGH');
  const [rootCause, setRootCause] = useState('');
  const [mitigationPlan, setMitigationPlan] = useState('');

  // Filter alerts
  const filteredAlerts = alerts.filter(a => {
    const matchesSev = selectedSeverity === 'ALL' || a.severity === selectedSeverity;
    const matchesStat = selectedAlertStatus === 'ALL' || a.status === selectedAlertStatus;
    return matchesSev && matchesStat;
  });

  const handleOpenActionModal = (alert?: AlertOut) => {
    if (alert) {
      setSelectedAlert(alert);
      setActionTitle(`Mitigate: ${alert.title}`);
      setActionDescription(alert.message);
      setPriority(alert.severity);
    } else {
      setSelectedAlert(null);
      setActionTitle('');
      setActionDescription('');
      setPriority('HIGH');
    }
    setRootCause('');
    setMitigationPlan('');
    setIsModalOpen(true);
  };

  const handleSaveAction = (e: React.FormEvent) => {
    e.preventDefault();
    onCreateAction({
      alert_id: selectedAlert?.alert_id,
      title: actionTitle,
      description: actionDescription,
      assigned_to: assignedTo,
      priority,
      root_cause: rootCause,
      mitigation_plan: mitigationPlan
    });
    if (selectedAlert) {
      onUpdateAlert(selectedAlert.alert_id, 'ACKNOWLEDGED');
    }
    setIsModalOpen(false);
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL': return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'HIGH': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'MEDIUM': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      default: return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'RESOLVED': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'IN_PROGRESS': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'ACKNOWLEDGED': return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      default: return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Incident Triage & Corrective Actions Hub</h1>
          <p className="text-xs text-slate-400 mt-1">
            Operational triage board for mitigating supply disruptions, assigning owners, and managing resolution workflows.
          </p>
        </div>
        <button
          onClick={() => handleOpenActionModal()}
          className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-lg shadow-brand-600/20 transition self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Create Corrective Action</span>
        </button>
      </div>

      {/* Navigation Tabs between Alerts and Corrective Actions */}
      <div className="flex border-b border-slate-800 space-x-6">
        <button
          onClick={() => setActiveTab('alerts')}
          className={`pb-3 text-xs font-bold border-b-2 transition flex items-center space-x-2 ${
            activeTab === 'alerts' 
              ? 'border-brand-500 text-brand-400' 
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <span>Active Operational Alerts</span>
          <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-[10px] text-slate-300">
            {alerts.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('actions')}
          className={`pb-3 text-xs font-bold border-b-2 transition flex items-center space-x-2 ${
            activeTab === 'actions' 
              ? 'border-brand-500 text-brand-400' 
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <span>Assigned Corrective Actions</span>
          <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-[10px] text-slate-300">
            {correctiveActions.length}
          </span>
        </button>
      </div>

      {/* VIEW 1: ALERTS LIST */}
      {activeTab === 'alerts' && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center gap-3 text-xs">
            <div className="flex items-center space-x-2">
              <span className="text-slate-400 font-medium">Severity:</span>
              <select
                value={selectedSeverity}
                onChange={(e) => setSelectedSeverity(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-300 focus:outline-none focus:border-brand-500"
              >
                <option value="ALL">All Severities</option>
                <option value="CRITICAL">Critical Only</option>
                <option value="HIGH">High Only</option>
                <option value="MEDIUM">Medium Only</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-slate-400 font-medium">Status:</span>
              <select
                value={selectedAlertStatus}
                onChange={(e) => setSelectedAlertStatus(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-300 focus:outline-none focus:border-brand-500"
              >
                <option value="ALL">All Statuses</option>
                <option value="ACTIVE">Active Incidents</option>
                <option value="ACKNOWLEDGED">Acknowledged</option>
                <option value="RESOLVED">Resolved</option>
              </select>
            </div>
          </div>

          {/* Alerts Card Feed */}
          <div className="space-y-3">
            {filteredAlerts.map((alert) => (
              <div 
                key={alert.alert_id} 
                className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition space-y-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${getSeverityBadge(alert.severity)}`}>
                        {alert.severity}
                      </span>
                      <span className="text-xs font-mono text-slate-400">{alert.alert_id}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 font-semibold">
                        {alert.entity_type}: {alert.entity_id}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getStatusBadge(alert.status)}`}>
                        {alert.status}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-white">{alert.title}</h3>
                  </div>

                  <div className="text-right shrink-0">
                    <div className="text-xs font-bold text-amber-400">${alert.impact_valuation.toLocaleString()}</div>
                    <div className="text-[10px] text-slate-500">Estimated Exposure</div>
                  </div>
                </div>

                <p className="text-xs text-slate-300 bg-slate-950/60 p-3 rounded-lg border border-slate-800/80 leading-relaxed font-sans">
                  {alert.message}
                </p>

                {/* Actions Buttons */}
                <div className="flex items-center justify-between pt-1 text-xs">
                  <span className="text-[10px] text-slate-500">
                    Created {new Date(alert.created_at).toLocaleString()}
                  </span>
                  <div className="flex items-center space-x-2">
                    {alert.status === 'ACTIVE' && (
                      <button
                        onClick={() => onUpdateAlert(alert.alert_id, 'ACKNOWLEDGED')}
                        className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                      >
                        Acknowledge
                      </button>
                    )}
                    {alert.status !== 'RESOLVED' && (
                      <>
                        <button
                          onClick={() => handleOpenActionModal(alert)}
                          className="px-3 py-1 rounded bg-brand-600/20 text-brand-400 hover:bg-brand-600/30 border border-brand-500/30 text-xs font-medium flex items-center space-x-1"
                        >
                          <UserPlus className="w-3.5 h-3.5" />
                          <span>Assign Action</span>
                        </button>
                        <button
                          onClick={() => onUpdateAlert(alert.alert_id, 'RESOLVED')}
                          className="px-3 py-1 rounded bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 border border-emerald-500/30 text-xs font-medium"
                        >
                          Resolve Alert
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* VIEW 2: CORRECTIVE ACTIONS TABLE */}
      {activeTab === 'actions' && (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden shadow-lg">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-medium uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="py-3 px-4">Action ID & Title</th>
                    <th className="py-3 px-4">Assigned Owner</th>
                    <th className="py-3 px-4 text-center">Priority</th>
                    <th className="py-3 px-4 text-center">Workflow Status</th>
                    <th className="py-3 px-4">Mitigation Protocol</th>
                    <th className="py-3 px-4 text-right">Quick Transition</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {correctiveActions.map((action) => (
                    <tr key={action.action_id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4 font-semibold text-white">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-xs text-brand-400">{action.action_id}</span>
                          {action.alert_id && (
                            <span className="text-[10px] text-slate-500">({action.alert_id})</span>
                          )}
                        </div>
                        <div className="text-xs text-slate-200 mt-0.5">{action.title}</div>
                      </td>
                      <td className="py-3 px-4 text-slate-300 font-medium">
                        {action.assigned_to}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getSeverityBadge(action.priority)}`}>
                          {action.priority}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getStatusBadge(action.status)}`}>
                          {action.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400 max-w-xs truncate">
                        {action.mitigation_plan || action.description}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {action.status !== 'RESOLVED' ? (
                          <div className="inline-flex space-x-1">
                            {action.status === 'OPEN' && (
                              <button
                                onClick={() => onUpdateAction(action.action_id, { status: 'IN_PROGRESS' })}
                                className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-blue-400 text-[10px] font-semibold"
                              >
                                Start Work
                              </button>
                            )}
                            <button
                              onClick={() => onUpdateAction(action.action_id, { status: 'RESOLVED', resolution_notes: 'Issue remediated; supply route secured.' })}
                              className="px-2 py-1 rounded bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 border border-emerald-500/30 text-[10px] font-semibold"
                            >
                              Resolve
                            </button>
                          </div>
                        ) : (
                          <span className="text-[11px] text-emerald-400 font-semibold flex items-center justify-end space-x-1">
                            <CheckCircle className="w-3.5 h-3.5" />
                            <span>Resolved</span>
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Create Corrective Action Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 space-y-4 shadow-2xl animate-in fade-in zoom-in duration-150">
            <h2 className="text-base font-bold text-white">Create Corrective Action Protocol</h2>
            
            <form onSubmit={handleSaveAction} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="text-slate-400 font-semibold">Action Title</label>
                <input
                  type="text"
                  required
                  value={actionTitle}
                  onChange={(e) => setActionTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-semibold">Assign Owner</label>
                <select
                  value={assignedTo}
                  onChange={(e) => setAssignedTo(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-brand-500"
                >
                  <option value="Lead Strategic Procurement Manager">Lead Strategic Procurement Manager</option>
                  <option value="Senior DI Engineer">Senior DI Engineer</option>
                  <option value="Quality Assurance Director">Quality Assurance Director</option>
                  <option value="Factory Operations Lead">Factory Operations Lead</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-semibold">Root Cause Hypothesis</label>
                <input
                  type="text"
                  placeholder="e.g. Inbound port congestion, raw resin shortage"
                  value={rootCause}
                  onChange={(e) => setRootCause(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-semibold">Mitigation Playbook</label>
                <textarea
                  rows={3}
                  placeholder="e.g. Trigger spot-buy purchase order, resequence Factory-US-01 work orders"
                  value={mitigationPlan}
                  onChange={(e) => setMitigationPlan(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white font-semibold"
                >
                  Confirm & Assign
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
