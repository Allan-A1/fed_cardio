import React, { useEffect, useRef } from 'react';
import { Activity, Play, Square, Download, CheckCircle } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { useApp } from '../context/AppContext';
import { useTrainingStatus, useTrainingLogs } from '../api/hooks';
import { api } from '../api/client';
import { SectionTitle } from '../components/UI';

const CUSTOM_TOOLTIP = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', padding: '10px 14px', fontSize: 13, boxShadow: 'var(--shadow-md)' }}>
      <p style={{ color: 'var(--text-muted)', marginBottom: 4 }}>Round {label}</p>
      {payload.map(p => (
        <p key={p.dataKey} style={{ color: p.color, fontWeight: 600 }}>{p.name}: {p.value?.toFixed ? p.value.toFixed(2) : p.value}</p>
      ))}
    </div>
  );
};

export default function TrainingPage() {
  const { clusters } = useApp();
  const termRef = useRef(null);

  // Joined cluster — pick first joined one, fallback to PCG
  const joinedCluster = clusters.find(c => c.joined) || clusters[0];

  // Real-time status from API
  const { data: statusData } = useTrainingStatus();
  const { data: logsData } = useTrainingLogs();

  const isRunning = statusData?.isRunning ?? false;
  const currentRound = statusData?.currentRound ?? 0;
  const localEpoch = statusData?.localEpoch ?? 0;
  const localAcc = statusData?.localAcc ?? 0;
  const logs = logsData?.logs ?? [];

  const [accuracyHistory, setAccuracyHistory] = React.useState([]);

  React.useEffect(() => {
    if (joinedCluster) {
      api.clusterMetrics(joinedCluster.id)
        .then((res) => setAccuracyHistory(res?.history || []))
        .catch((err) => console.error('Failed loading metrics history:', err));
    }
  }, [joinedCluster?.id]);

  // Auto-scroll terminal
  useEffect(() => {
    if (termRef.current) termRef.current.scrollTop = termRef.current.scrollHeight;
  }, [logs]);

  async function handleStart() {
    if (!joinedCluster) return;
    try {
      await api.startTraining(joinedCluster.id);
    } catch (e) {
      console.error('Start training failed:', e);
    }
  }

  async function handleStop() {
    try {
      await api.stopTraining();
    } catch (e) {
      console.error('Stop training failed:', e);
    }
  }

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header">
        <h1 className="page-title">Training Status</h1>
        <p className="page-subtitle">Monitor your local federated learning training process and global model synchronization in real time.</p>
      </div>

      {/* Status Banner */}
      <div
        id="training-status-banner"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: 'var(--sp-4) var(--sp-6)',
          background: isRunning ? 'hsla(210,100%,56%,0.08)' : 'hsla(220,20%,30%,0.08)',
          border: `1px solid ${isRunning ? 'hsla(210,100%,56%,0.2)' : 'var(--border-subtle)'}`,
          borderRadius: 'var(--radius-lg)',
          marginBottom: 'var(--sp-6)',
          flexWrap: 'wrap',
          gap: 'var(--sp-4)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-4)' }}>
          <div style={{ width: 10, height: 10, borderRadius: '50%', background: isRunning ? 'var(--brand-primary)' : 'var(--text-muted)', animation: isRunning ? 'pulse-dot 1s infinite' : 'none' }} />
          <div>
            <div style={{ fontWeight: 700, fontSize: 15 }}>
              {isRunning
                ? `Round ${currentRound} — Local Training Active`
                : joinedCluster ? 'Training Paused' : 'No Cluster Joined'}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
              {isRunning
                ? `${statusData?.clusterId ?? ''} · Epoch ${localEpoch} · Local Acc: ${localAcc}%`
                : joinedCluster
                  ? 'Click Start to begin local training'
                  : 'Join a cluster on the Clusters page first'}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 'var(--sp-3)' }}>
          {isRunning ? (
            <button id="btn-stop-training" className="btn btn-danger" onClick={handleStop}>
              <Square size={14} /> Pause
            </button>
          ) : (
            <button
              id="btn-start-training"
              className="btn btn-primary"
              onClick={handleStart}
              disabled={!joinedCluster}
            >
              <Play size={14} /> Start Training
            </button>
          )}
          <button id="btn-download-model" className="btn btn-secondary">
            <Download size={14} /> Download Global Model
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid-4 mb-6">
        {[
          { label: 'Current FL Round', value: currentRound > 0 ? currentRound : '—', sub: 'of 50 total', color: 'var(--brand-primary)' },
          { label: 'Global Model Accuracy', value: joinedCluster ? `${joinedCluster.globalAccuracy}%` : '—', sub: 'From last training run', color: 'var(--brand-success)' },
          { label: 'Your Local Accuracy', value: localAcc > 0 ? `${localAcc}%` : '—', sub: localEpoch > 0 ? `Epoch ${localEpoch}` : 'Not started', color: 'var(--brand-secondary)' },
          { label: 'Active Cluster', value: statusData?.clusterId ?? (joinedCluster?.modality ?? '—'), sub: joinedCluster?.name ?? 'None joined', color: 'var(--brand-accent)' },
        ].map((m, i) => (
          <div key={i} className="card" style={{ textAlign: 'center' }} id={`metric-card-${i}`}>
            <div style={{ fontSize: 28, fontWeight: 800, color: m.color, letterSpacing: '-0.02em' }}>{m.value}</div>
            <div style={{ fontSize: 13, fontWeight: 600, marginTop: 4 }}>{m.label}</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{m.sub}</div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid-2 mb-6">
        <div className="card" id="chart-training-accuracy">
          <SectionTitle icon={Activity}>Accuracy Over Rounds</SectionTitle>
          {accuracyHistory.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={accuracyHistory} margin={{ top: 5, right: 10, bottom: 5, left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
                <XAxis dataKey="round" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: 'var(--text-muted)' }} unit="%" />
                <Tooltip content={<CUSTOM_TOOLTIP />} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="global" stroke="hsl(210,100%,56%)" strokeWidth={2.5} dot={false} name="Global" />
                <Line type="monotone" dataKey="local" stroke="hsl(145,65%,50%)" strokeWidth={2} strokeDasharray="5 3" dot={false} name="Your Local" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
              No training history yet — start training to see results here
            </div>
          )}
        </div>

        <div className="card" id="chart-training-loss">
          <SectionTitle icon={Activity}>Loss Over Rounds</SectionTitle>
          <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
            No loss history yet — start training to see results here
          </div>
        </div>
      </div>

      {/* FL Round Timeline */}
      <div className="card mb-6" id="card-fl-timeline">
        <SectionTitle icon={CheckCircle}>FL Round Timeline</SectionTitle>
        <div style={{ display: 'flex', gap: 'var(--sp-4)', overflowX: 'auto', paddingBottom: 'var(--sp-2)' }}>
          {[
            { label: 'Global Weights Received', done: isRunning || currentRound > 0 },
            { label: 'Local Training Started', done: isRunning },
            { label: 'DP Noise Applied', done: isRunning && localEpoch >= 3 },
            { label: 'Model Update Uploaded', done: !isRunning && currentRound > 0 },
            { label: 'Server Aggregation', done: false },
            { label: 'New Global Model', done: false },
          ].map((step, i) => (
            <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, minWidth: 110 }}>
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: step.done ? 'var(--brand-success)' : 'var(--bg-elevated)', border: `2px solid ${step.done ? 'var(--brand-success)' : 'var(--border-default)'}`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {step.done ? <CheckCircle size={16} color="white" /> : <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{i + 1}</span>}
              </div>
              <span style={{ fontSize: 11, color: step.done ? 'var(--text-primary)' : 'var(--text-muted)', textAlign: 'center', lineHeight: 1.3 }}>{step.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Live Logs */}
      <div className="card" id="card-training-logs">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-4)' }}>
          <SectionTitle icon={Activity}>Live Training Logs</SectionTitle>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-3)' }}>
            {isRunning && (
              <span style={{ fontSize: 11, color: 'var(--brand-primary)', display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--brand-primary)', display: 'inline-block', animation: 'pulse-dot 1s infinite' }} />
                Live
              </span>
            )}
          </div>
        </div>
        <div
          ref={termRef}
          style={{ maxHeight: 300, overflowY: 'auto', background: 'hsl(220,18%,97%)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', padding: 'var(--sp-4)', fontFamily: 'var(--font-mono)', fontSize: 12, lineHeight: 1.8 }}
        >
          {logs.length === 0 ? (
            <span style={{ color: 'var(--text-muted)' }}>Waiting for training to start...</span>
          ) : logs.map((l, i) => {
            const colorMap = { info: 'var(--brand-secondary)', success: 'var(--brand-success)', warning: 'var(--brand-warning)', error: 'var(--brand-danger)' };
            return (
              <div key={i} style={{ display: 'flex', gap: 'var(--sp-3)' }}>
                <span style={{ color: 'var(--text-muted)', flexShrink: 0 }}>[{l.time}]</span>
                <span style={{ color: colorMap[l.type] || colorMap.info }}>{l.msg}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
