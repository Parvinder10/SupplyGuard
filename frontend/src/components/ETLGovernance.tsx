import React, { useState } from 'react';
import { 
  GitBranch, 
  CheckCircle2, 
  AlertCircle, 
  XCircle, 
  Clock, 
  Database, 
  ShieldCheck, 
  FileWarning, 
  ArrowRight 
} from 'lucide-react';
import { ETLAuditLogOut, ETLRejectedRecordOut, DataQualityTestOut } from '../types';

interface ETLGovernanceProps {
  auditLogs: ETLAuditLogOut[];
  rejectedRecords: ETLRejectedRecordOut[];
  dqResults: DataQualityTestOut[];
}

export const ETLGovernance: React.FC<ETLGovernanceProps> = ({
  auditLogs,
  rejectedRecords,
  dqResults
}) => {
  const [activeSection, setActiveSection] = useState<'audit' | 'rejected' | 'quality'>('audit');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">ETL Governance, Audit Logs & Data Quality</h1>
        <p className="text-xs text-slate-400 mt-1">
          End-to-end lineage telemetry, Apache Airflow execution logs, dead-letter rejected record inspector, and automated DQ assertions.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 space-x-6 text-xs font-bold">
        <button
          onClick={() => setActiveSection('audit')}
          className={`pb-3 border-b-2 transition flex items-center space-x-2 ${
            activeSection === 'audit'
              ? 'border-brand-500 text-brand-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <GitBranch className="w-4 h-4" />
          <span>Pipeline Run Audit Logs ({auditLogs.length})</span>
        </button>

        <button
          onClick={() => setActiveSection('rejected')}
          className={`pb-3 border-b-2 transition flex items-center space-x-2 ${
            activeSection === 'rejected'
              ? 'border-brand-500 text-brand-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileWarning className="w-4 h-4" />
          <span>Dead-Letter Rejections ({rejectedRecords.length})</span>
        </button>

        <button
          onClick={() => setActiveSection('quality')}
          className={`pb-3 border-b-2 transition flex items-center space-x-2 ${
            activeSection === 'quality'
              ? 'border-brand-500 text-brand-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>Automated Data Quality Assertions ({dqResults.length})</span>
        </button>
      </div>

      {/* SECTION 1: AUDIT LOGS */}
      {activeSection === 'audit' && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-medium uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">Pipeline Name</th>
                  <th className="py-3 px-4">Batch ID</th>
                  <th className="py-3 px-4">Execution Time</th>
                  <th className="py-3 px-4 text-center">Duration</th>
                  <th className="py-3 px-4 text-center">Rows Extracted</th>
                  <th className="py-3 px-4 text-center">Rows Loaded</th>
                  <th className="py-3 px-4 text-center">Rows Rejected</th>
                  <th className="py-3 px-4 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {auditLogs.map((log) => (
                  <tr key={log.run_id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-sans font-semibold text-white">
                      {log.pipeline_name}
                    </td>
                    <td className="py-3 px-4 text-slate-400">{log.batch_id || '-'}</td>
                    <td className="py-3 px-4 text-slate-400">
                      {new Date(log.start_time).toLocaleTimeString()}
                    </td>
                    <td className="py-3 px-4 text-center text-slate-300">
                      {log.duration_seconds.toFixed(1)}s
                    </td>
                    <td className="py-3 px-4 text-center text-white">
                      {log.rows_extracted.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-center text-emerald-400 font-bold">
                      {log.rows_loaded.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className={log.rows_rejected > 0 ? 'text-red-400 font-bold' : 'text-slate-600'}>
                        {log.rows_rejected}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-sans">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                        {log.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SECTION 2: DEAD-LETTER REJECTED RECORDS */}
      {activeSection === 'rejected' && (
        <div className="space-y-3">
          <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-400 text-xs flex items-center space-x-2">
            <FileWarning className="w-4 h-4 shrink-0" />
            <span>
              Dead-letter queue isolates corrupt records with schema mismatches or business logic errors, allowing downstream pipelines to proceed without failure.
            </span>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden shadow-lg">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-medium uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="py-3 px-4">Rejection ID</th>
                    <th className="py-3 px-4">Source Table</th>
                    <th className="py-3 px-4">Error Code</th>
                    <th className="py-3 px-4">Diagnostic Reason</th>
                    <th className="py-3 px-4">Raw Inbound Payload</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {rejectedRecords.map((rec) => (
                    <tr key={rec.rejection_id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4 font-mono text-slate-400">#{rec.rejection_id}</td>
                      <td className="py-3 px-4 font-semibold text-white">{rec.source_table}</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/20 text-red-400 border border-red-500/30 font-mono">
                          {rec.error_code}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-red-300 font-medium">{rec.error_reason}</td>
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-400 max-w-sm truncate">
                        {rec.payload}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* SECTION 3: DATA QUALITY ASSERTIONS */}
      {activeSection === 'quality' && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-medium uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">Assertion Rule</th>
                  <th className="py-3 px-4">Target Warehouse Table</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4 text-center">Severity</th>
                  <th className="py-3 px-4 text-center">Metric vs Threshold</th>
                  <th className="py-3 px-4 text-center">Result</th>
                  <th className="py-3 px-4">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {dqResults.map((dq) => (
                  <tr key={dq.test_id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-mono font-semibold text-white">
                      {dq.test_name}
                    </td>
                    <td className="py-3 px-4 text-slate-300">{dq.target_table}</td>
                    <td className="py-3 px-4 font-mono text-slate-400">{dq.assertion_type}</td>
                    <td className="py-3 px-4 text-center">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        dq.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'
                      }`}>
                        {dq.severity}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center font-mono">
                      {dq.metric_value} (max {dq.threshold})
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center space-x-1 w-fit mx-auto">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>{dq.status}</span>
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400">{dq.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
