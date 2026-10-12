import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Printer,
  Download,
  Share2,
  Calendar,
  Clock,
  User,
  Heart,
  Activity,
  FileCheck,
  RefreshCw,
  Cpu,
  ShieldCheck,
  AlertTriangle,
} from 'lucide-react';
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';

import { api } from '../api/client';
import ResultBadge from '../components/ResultBadge';
import ConfidenceBar from '../components/ConfidenceBar';
import FlagList from '../components/FlagList';
import WaveformPlayer from '../components/WaveformPlayer';
import EchoViewer from '../components/EchoViewer';
import DecisionPanel from '../components/DecisionPanel';

export default function ReportPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isExporting, setIsExporting] = useState(false);

  const fetchReport = async () => {
    try {
      setLoading(true);
      const data = await api.screeningReport(id);
      setReport(data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('Could not load the requested screening report.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [id]);

  const handleEscalate = async (payload) => {
    await api.escalateReport(id, payload);
    await fetchReport();
  };

  const handleDismiss = async (payload) => {
    await api.dismissReport(id, payload);
    await fetchReport();
  };

  // Phase 5: PDF Export using html2canvas and jsPDF
  const handleExportPDF = async () => {
    setIsExporting(true);
    try {
      const element = document.getElementById('printable-report');
      if (!element) return;

      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        logging: false,
        backgroundColor: '#ffffff',
      });

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;

      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
      pdf.save(`Screening_Report_${report.patient_id}_${report.report_id}.pdf`);
    } catch (err) {
      console.error('PDF export error:', err);
      // Fallback: browser print dialog
      window.print();
    } finally {
      setIsExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="page-container" style={{ textAlign: 'center', padding: '80px 0' }}>
        <RefreshCw size={36} className="animate-spin" color="var(--brand-primary)" style={{ margin: '0 auto 16px' }} />
        <h3 style={{ fontSize: '18px', fontWeight: '700', color: 'var(--text-primary)' }}>
          Retrieving Clinical Screening Report...
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Loading Grad-CAM saliency tensors and signal telemetry</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="page-container" style={{ textAlign: 'center', padding: '80px 0' }}>
        <AlertTriangle size={48} color="var(--brand-danger)" style={{ margin: '0 auto 16px' }} />
        <h3 style={{ fontSize: '20px', fontWeight: '700', color: 'var(--text-primary)' }}>
          Report Not Found
        </h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
          {error || `No screening report exists with ID: ${id}`}
        </p>
        <Link to="/screening" className="btn btn-primary">
          Back to New Screening
        </Link>
      </div>
    );
  }

  const isPCG = report.modality === 'PCG';
  const audioUrl = report.audio_url || api.audioUrl(report.report_id);
  const edFrameUrl = report.ed_frame_url || api.frameUrl(report.report_id, 'ed');
  const esFrameUrl = report.es_frame_url || api.frameUrl(report.report_id, 'es');

  return (
    <div className="page-container animate-fade-in" style={{ maxWidth: '1100px', margin: '0 auto' }}>
      {/* Navigation Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
          marginBottom: '20px',
        }}
      >
        <Link
          to="/screening"
          className="btn btn-ghost"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)' }}
        >
          <ArrowLeft size={16} />
          Back to Screening Form
        </Link>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            className="btn btn-outline"
            onClick={handleExportPDF}
            disabled={isExporting}
            id="btn-export-pdf"
            style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}
          >
            {isExporting ? <RefreshCw size={15} className="animate-spin" /> : <Printer size={15} />}
            {isExporting ? 'Generating PDF...' : 'Export Clinical PDF'}
          </button>
        </div>
      </div>

      {/* Printable Report Canvas Area */}
      <div id="printable-report">
        {/* Patient & Report Metadata Header Card */}
        <div
          className="card"
          style={{
            padding: '24px 28px',
            marginBottom: '20px',
            background: 'var(--bg-surface)',
            borderLeft: `4px solid ${
              report.prediction === 'Abnormal' ? 'var(--brand-danger)' : 'var(--brand-success)'
            }`,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                <span style={{ fontSize: '24px', fontWeight: '800', color: 'var(--text-primary)' }}>
                  {report.patient_name}
                </span>
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '13px',
                    fontWeight: '700',
                    color: 'var(--brand-primary)',
                    background: 'hsla(221, 100%, 55%, 0.1)',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-sm)',
                  }}
                >
                  {report.patient_id}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap', fontSize: '13px', color: 'var(--text-secondary)' }}>
                <span><strong>Age Group:</strong> {report.age_group}</span>
                <span>•</span>
                <span><strong>Modality:</strong> {report.modality}</span>
                <span>•</span>
                <span><strong>Report ID:</strong> {report.report_id}</span>
                <span>•</span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                  <Calendar size={13} />
                  {new Date(report.created_at).toLocaleDateString()} {new Date(report.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>

            {/* Triage Recommendation Pill */}
            <div
              style={{
                padding: '8px 16px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                textAlign: 'right',
              }}
            >
              <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)', fontWeight: '700' }}>
                Automated Triage Guidance
              </div>
              <div style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)', marginTop: '2px' }}>
                {report.triage_recommendation}
              </div>
            </div>
          </div>
        </div>

        {/* Primary Classification & Confidence Row */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '20px',
            marginBottom: '20px',
          }}
        >
          <ResultBadge
            prediction={report.prediction}
            modality={report.modality}
            efValue={report.ef_value}
            confidence={report.confidence}
            size="large"
          />

          <ConfidenceBar
            confidence={report.confidence}
            prediction={report.prediction}
          />
        </div>

        {/* Flag Signals Section */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <AlertTriangle size={18} color="var(--brand-warning)" />
            <h3 style={{ fontSize: '16px', fontWeight: '800', color: 'var(--text-primary)', margin: 0 }}>
              Clinical Quality & Risk Flags ({report.flags ? report.flags.length : 0})
            </h3>
          </div>
          <FlagList flags={report.flags} />
        </div>

        {/* Modality Specific Explainability View */}
        <div style={{ marginBottom: '24px' }}>
          {isPCG ? (
            <div>
              <WaveformPlayer
                audioUrl={audioUrl}
                xaiSegments={report.xai_segments || []}
              />

              {/* Explainability Breakdown Card */}
              {report.xai_segments && report.xai_segments.length > 0 && (
                <div
                  className="card"
                  style={{
                    padding: '16px 20px',
                    marginTop: '12px',
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <ShieldCheck size={18} color="var(--brand-primary)" />
                    <span style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text-primary)' }}>
                      Grad-CAM Explainable AI (XAI) Murmur Localization Summary
                    </span>
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
                    The 2D-CNN feature extraction network (block3 conv layer) localized {report.xai_segments.length} high-gradient temporal window(s) that strongly shifted classification towards <strong>Abnormal (Murmur)</strong>. The primary energy concentration occurs between <strong>{report.xai_segments[0].start_sec.toFixed(1)}s and {report.xai_segments[0].end_sec.toFixed(1)}s</strong>, matching the acoustic frequencies of turbulent systolic regurgitation.
                  </p>
                </div>
              )}
            </div>
          ) : (
            <EchoViewer
              edFrameUrl={edFrameUrl}
              esFrameUrl={esFrameUrl}
              efValue={report.ef_value}
              prediction={report.prediction}
            />
          )}
        </div>

        {/* Model Architecture & Audit Telemetry */}
        <div
          className="card"
          style={{
            padding: '16px 20px',
            marginBottom: '24px',
            background: 'hsl(210, 25%, 98%)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <Cpu size={16} color="var(--text-secondary)" />
            <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Model Telemetry & Pipeline Audit
            </span>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '12px',
              fontSize: '12px',
              color: 'var(--text-secondary)',
            }}
          >
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Architecture:</span>{' '}
              <strong>{isPCG ? 'PCGNet (2D-CNN mel-spectrogram)' : 'EchoNet (4-block 2-channel CNN)'}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Checkpoint:</span>{' '}
              <strong>{isPCG ? 'pcg_best.pt (FedMed Baseline)' : 'echo_best.pt (EchoNet-Pediatric)'}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Input Resolution:</span>{' '}
              <strong>{isPCG ? '64 Mel bins × 4000 Hz' : '112×112 Biplane (ED+ES)'}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Triage Status:</span>{' '}
              <strong style={{ textTransform: 'capitalize' }}>{report.status || 'Pending'}</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Decision Action Panel */}
      <DecisionPanel
        reportId={report.report_id}
        currentStatus={report.status}
        doctorNotes={report.doctor_notes}
        technicianNotes={report.technician_notes}
        onEscalate={handleEscalate}
        onDismiss={handleDismiss}
      />
    </div>
  );
}
