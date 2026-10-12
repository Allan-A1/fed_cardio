import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Search,
  Filter,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  Heart,
  Activity,
  RefreshCw,
  PlusCircle,
  Users,
  ShieldAlert,
} from 'lucide-react';
import { api } from '../api/client';
import { StatCard } from '../components/UI';

export default function HistoryPage() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Search & filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [modalityFilter, setModalityFilter] = useState('ALL');
  const [resultFilter, setResultFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const fetchReports = async () => {
    try {
      setLoading(true);
      const data = await api.screeningReports();
      setReports(data || []);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('Failed to load past screening reports.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  // Filtered reports calculation
  const filteredReports = reports.filter((r) => {
    // Search query matches name, patient_id, or report_id
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const match =
        (r.patient_name || '').toLowerCase().includes(q) ||
        (r.patient_id || '').toLowerCase().includes(q) ||
        (r.report_id || '').toLowerCase().includes(q);
      if (!match) return false;
    }

    // Modality filter
    if (modalityFilter !== 'ALL' && (r.modality || '').toUpperCase() !== modalityFilter) {
      return false;
    }

    // Result filter
    if (resultFilter !== 'ALL' && (r.prediction || '').toUpperCase() !== resultFilter) {
      return false;
    }

    // Status filter
    if (statusFilter !== 'ALL' && (r.status || '').toUpperCase() !== statusFilter) {
      return false;
    }

    return true;
  });

  // Calculate summary metrics
  const totalCount = reports.length;
  const abnormalCount = reports.filter((r) => (r.prediction || '').toLowerCase() === 'abnormal').length;
  const escalatedCount = reports.filter((r) => (r.status || '').toLowerCase() === 'escalated').length;
  const avgConf =
    totalCount > 0
      ? (reports.reduce((acc, r) => acc + (r.confidence || 0), 0) / totalCount) * 100
      : 0;

  return (
    <div className="page-container animate-fade-in">
      {/* Page Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
          marginBottom: '24px',
        }}
      >
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: '800', color: 'var(--text-primary)', margin: 0 }}>
            Patient Screening Registry & History
          </h1>
          <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Complete audit trail of pediatric PCG heart sound & echocardiogram triage reports
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            className="btn btn-outline"
            onClick={fetchReports}
            title="Refresh history list"
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>

          <Link
            to="/screening"
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <PlusCircle size={16} />
            New Screening
          </Link>
        </div>
      </div>

      {/* Metric Stat Cards Strip */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '16px',
          marginBottom: '24px',
        }}
      >
        <StatCard
          icon={Users}
          iconColor="var(--brand-primary)"
          iconBg="hsla(221, 100%, 55%, 0.1)"
          value={totalCount}
          label="Total Patients Screened"
          glowColor="hsla(221, 100%, 55%, 0.08)"
          id="stat-total-screened"
        />

        <StatCard
          icon={AlertTriangle}
          iconColor="var(--brand-danger)"
          iconBg="hsla(0, 84%, 60%, 0.1)"
          value={abnormalCount}
          label="Abnormal Findings Flagged"
          glowColor="hsla(0, 84%, 60%, 0.08)"
          id="stat-abnormal-screened"
        />

        <StatCard
          icon={ShieldAlert}
          iconColor="hsl(35, 95%, 48%)"
          iconBg="hsla(35, 95%, 52%, 0.12)"
          value={escalatedCount}
          label="Escalated to Cardiologist"
          glowColor="hsla(35, 95%, 52%, 0.08)"
          id="stat-escalated-screened"
        />

        <StatCard
          icon={Activity}
          iconColor="var(--brand-success)"
          iconBg="hsla(142, 70%, 42%, 0.1)"
          value={`${avgConf.toFixed(1)}%`}
          label="Average AI Confidence"
          glowColor="hsla(142, 70%, 42%, 0.08)"
          id="stat-avg-confidence"
        />
      </div>

      {/* Filter and Search Bar Card */}
      <div
        className="card"
        style={{
          padding: '16px 20px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '14px',
        }}
      >
        {/* Search input */}
        <div style={{ position: 'relative', flex: '1 1 260px', minWidth: '220px' }}>
          <Search
            size={16}
            color="var(--text-muted)"
            style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }}
          />
          <input
            type="text"
            className="input"
            placeholder="Search patient name, ID, or report..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ paddingLeft: '36px', width: '100%' }}
          />
        </div>

        {/* Filter Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {/* Modality */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)' }}>Modality:</span>
            {['ALL', 'PCG', 'ECHO'].map((m) => (
              <button
                key={m}
                className={`btn btn-sm ${modalityFilter === m ? 'btn-primary' : 'btn-ghost'}`}
                style={{ fontSize: '11px', padding: '4px 8px' }}
                onClick={() => setModalityFilter(m)}
              >
                {m}
              </button>
            ))}
          </div>

          <div style={{ width: '1px', height: '20px', background: 'var(--border-subtle)' }} />

          {/* Result */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)' }}>Result:</span>
            {['ALL', 'ABNORMAL', 'NORMAL'].map((res) => (
              <button
                key={res}
                className={`btn btn-sm ${resultFilter === res ? 'btn-primary' : 'btn-ghost'}`}
                style={{ fontSize: '11px', padding: '4px 8px' }}
                onClick={() => setResultFilter(res)}
              >
                {res}
              </button>
            ))}
          </div>

          <div style={{ width: '1px', height: '20px', background: 'var(--border-subtle)' }} />

          {/* Status */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)' }}>Status:</span>
            {['ALL', 'ESCALATED', 'DISMISSED', 'PENDING'].map((st) => (
              <button
                key={st}
                className={`btn btn-sm ${statusFilter === st ? 'btn-primary' : 'btn-ghost'}`}
                style={{ fontSize: '11px', padding: '4px 8px' }}
                onClick={() => setStatusFilter(st)}
              >
                {st}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Registry Table Card */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading && reports.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
            <RefreshCw size={28} className="animate-spin" style={{ margin: '0 auto 12px' }} />
            <span>Loading screening registry...</span>
          </div>
        ) : filteredReports.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
            <FileText size={36} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
            <h4 style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '4px' }}>
              No Screening Reports Found
            </h4>
            <p style={{ fontSize: '13px', margin: 0 }}>
              {searchQuery || modalityFilter !== 'ALL' || resultFilter !== 'ALL'
                ? 'Try adjusting your search query or filters.'
                : 'No patients have been screened yet. Click "New Screening" to begin.'}
            </p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: 'var(--bg-elevated)', borderBottom: '1px solid var(--border-default)' }}>
                  <th style={{ padding: '14px 18px', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Patient Info
                  </th>
                  <th style={{ padding: '14px 18px', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Modality
                  </th>
                  <th style={{ padding: '14px 18px', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    AI Classification
                  </th>
                  <th style={{ padding: '14px 18px', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Confidence
                  </th>
                  <th style={{ padding: '14px 18px', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Flags
                  </th>
                  <th style={{ padding: '14px 18px', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Date
                  </th>
                  <th style={{ padding: '14px 18px', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Triage Status
                  </th>
                  <th style={{ padding: '14px 18px', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', textAlign: 'right' }}>
                    Action
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredReports.map((row) => {
                  const isAbnormal = (row.prediction || '').toLowerCase() === 'abnormal';
                  const isEscalated = (row.status || '').toLowerCase() === 'escalated';
                  const isDismissed = (row.status || '').toLowerCase() === 'dismissed';

                  return (
                    <tr
                      key={row.report_id}
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        transition: 'background var(--transition-fast)',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = 'hsl(210, 20%, 98%)')}
                      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                    >
                      {/* Patient Info */}
                      <td style={{ padding: '14px 18px' }}>
                        <div style={{ fontWeight: '700', color: 'var(--text-primary)', fontSize: '14px' }}>
                          {row.patient_name}
                        </div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                          {row.patient_id} • {row.age_group}
                        </div>
                      </td>

                      {/* Modality */}
                      <td style={{ padding: '14px 18px' }}>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '5px',
                            fontSize: '12px',
                            fontWeight: '700',
                            padding: '3px 8px',
                            borderRadius: 'var(--radius-sm)',
                            background:
                              row.modality === 'PCG'
                                ? 'hsla(355, 80%, 60%, 0.1)'
                                : 'hsla(265, 80%, 65%, 0.1)',
                            color:
                              row.modality === 'PCG'
                                ? 'hsl(355, 80%, 50%)'
                                : 'hsl(265, 80%, 55%)',
                          }}
                        >
                          {row.modality === 'PCG' ? <Heart size={13} /> : <Activity size={13} />}
                          {row.modality}
                        </span>
                      </td>

                      {/* AI Classification */}
                      <td style={{ padding: '14px 18px' }}>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '5px',
                            fontSize: '12px',
                            fontWeight: '700',
                            padding: '4px 10px',
                            borderRadius: 'var(--radius-full)',
                            background: isAbnormal
                              ? 'hsla(0, 84%, 60%, 0.12)'
                              : 'hsla(142, 70%, 42%, 0.12)',
                            color: isAbnormal ? 'hsl(0, 75%, 45%)' : 'hsl(142, 70%, 30%)',
                          }}
                        >
                          {isAbnormal ? <AlertTriangle size={13} /> : <CheckCircle2 size={13} />}
                          {row.prediction}
                        </span>
                      </td>

                      {/* Confidence */}
                      <td style={{ padding: '14px 18px', fontWeight: '700', fontSize: '13px', color: 'var(--text-primary)' }}>
                        {Math.round((row.confidence || 0) * 100)}%
                      </td>

                      {/* Flags count */}
                      <td style={{ padding: '14px 18px' }}>
                        {row.flags_count > 0 ? (
                          <span
                            style={{
                              fontSize: '11px',
                              fontWeight: '700',
                              color: 'hsl(35, 95%, 40%)',
                              background: 'hsla(35, 95%, 52%, 0.12)',
                              padding: '2px 7px',
                              borderRadius: 'var(--radius-full)',
                            }}
                          >
                            {row.flags_count} flag{row.flags_count > 1 ? 's' : ''}
                          </span>
                        ) : (
                          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>0</span>
                        )}
                      </td>

                      {/* Date */}
                      <td style={{ padding: '14px 18px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                        {new Date(row.created_at).toLocaleDateString()}
                      </td>

                      {/* Status */}
                      <td style={{ padding: '14px 18px' }}>
                        <span
                          style={{
                            fontSize: '11px',
                            fontWeight: '700',
                            padding: '3px 8px',
                            borderRadius: 'var(--radius-full)',
                            background: isEscalated
                              ? 'hsla(0, 84%, 60%, 0.12)'
                              : isDismissed
                              ? 'hsla(142, 70%, 42%, 0.12)'
                              : 'var(--bg-elevated)',
                            color: isEscalated
                              ? 'hsl(0, 75%, 45%)'
                              : isDismissed
                              ? 'hsl(142, 70%, 30%)'
                              : 'var(--text-muted)',
                            textTransform: 'capitalize',
                          }}
                        >
                          {row.status || 'Pending'}
                        </span>
                      </td>

                      {/* Action */}
                      <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                        <Link
                          to={`/screening/report/${row.report_id}`}
                          className="btn btn-sm btn-outline"
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '5px',
                            fontWeight: '700',
                            fontSize: '12px',
                          }}
                        >
                          <span>View</span>
                          <ArrowRight size={13} />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
