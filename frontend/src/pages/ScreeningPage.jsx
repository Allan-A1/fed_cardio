import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UploadCloud,
  FileAudio,
  FileVideo,
  Sparkles,
  ArrowRight,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  HelpCircle,
  Heart,
  Activity,
  User,
} from 'lucide-react';
import { api } from '../api/client';

const AGE_GROUPS = [
  { id: 'Neonate', label: 'Neonate (0–28d)', risk: 'High-sensitivity' },
  { id: 'Infant', label: 'Infant (1–12m)', risk: 'Pediatric' },
  { id: 'Child', label: 'Child (1–12y)', risk: 'Standard' },
  { id: 'Adolescent', label: 'Adolescent (13–18y)', risk: 'Standard' },
];

export default function ScreeningPage() {
  const navigate = useNavigate();

  const [patientId, setPatientId] = useState('');
  const [patientName, setPatientName] = useState('');
  const [ageGroup, setAgeGroup] = useState('Child');
  const [modality, setModality] = useState('PCG');
  const [notes, setNotes] = useState('');

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewAudioUrl, setPreviewAudioUrl] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const [demoSamples, setDemoSamples] = useState([]);
  const [selectedDemoId, setSelectedDemoId] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStep, setSubmitStep] = useState(0);
  const [errorMessage, setErrorMessage] = useState(null);

  const fileInputRef = useRef(null);

  // Auto-generate random patient ID on first mount
  const generateRandomPatientId = () => {
    const num = Math.floor(1000 + Math.random() * 9000);
    setPatientId(`P-${num}`);
  };

  useEffect(() => {
    generateRandomPatientId();
    // Load pre-built demo samples from backend
    api.demoSamples()
      .then((data) => setDemoSamples(data || []))
      .catch((err) => console.error('Failed to load demo samples:', err));
  }, []);

  // Handle preset sample selection
  const handleSelectDemo = (sample) => {
    setSelectedDemoId(sample.sample_id);
    setPatientName(sample.patient_name);
    setAgeGroup(sample.age_group);
    setModality(sample.modality);
    setSelectedFile(null);
    if (previewAudioUrl) {
      URL.revokeObjectURL(previewAudioUrl);
      setPreviewAudioUrl(null);
    }
  };

  // Handle local file selection
  const handleFileChange = (file) => {
    if (!file) return;

    const ext = file.name.split('.').pop().toLowerCase();
    if (modality === 'PCG' && ext !== 'wav') {
      setErrorMessage('Please select a valid .wav audio file for PCG screening.');
      return;
    }
    if (modality === 'Echo' && ext !== 'avi') {
      setErrorMessage('Please select a valid .avi video file for Echo screening.');
      return;
    }

    setErrorMessage(null);
    setSelectedFile(file);
    setSelectedDemoId('');

    if (modality === 'PCG') {
      if (previewAudioUrl) URL.revokeObjectURL(previewAudioUrl);
      const url = URL.createObjectURL(file);
      setPreviewAudioUrl(url);
    } else {
      setPreviewAudioUrl(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  // Run screening form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!patientId.trim()) {
      setErrorMessage('Patient ID is required.');
      return;
    }
    if (!patientName.trim()) {
      setErrorMessage('Patient Name is required.');
      return;
    }
    if (!selectedFile && !selectedDemoId) {
      setErrorMessage('Please select an audio/video file or pick a Clinical Demo preset.');
      return;
    }

    setIsSubmitting(true);
    setSubmitStep(1);

    // Multi-step animated progress simulation
    const stepTimer1 = setTimeout(() => setSubmitStep(2), 700);
    const stepTimer2 = setTimeout(() => setSubmitStep(3), 1500);

    try {
      const formData = new FormData();
      formData.append('patient_id', patientId);
      formData.append('patient_name', patientName);
      formData.append('age_group', ageGroup);
      formData.append('modality', modality);
      formData.append('notes', notes);
      if (selectedDemoId) {
        formData.append('demo_sample_id', selectedDemoId);
      }
      if (selectedFile) {
        formData.append('file', selectedFile);
      }

      const report = await api.uploadScreening(formData);
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      setSubmitStep(4);

      setTimeout(() => {
        navigate(`/screening/report/${report.report_id}`);
      }, 500);
    } catch (err) {
      console.error(err);
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      setErrorMessage(err.message || 'Screening analysis failed. Please try again.');
      setIsSubmitting(false);
      setSubmitStep(0);
    }
  };

  return (
    <div className="page-container animate-fade-in" style={{ maxWidth: '1000px', margin: '0 auto' }}>
      {/* Top Banner */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--brand-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
            }}
          >
            <Heart size={20} />
          </div>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: '800', color: 'var(--text-primary)', margin: 0 }}>
              New Pediatric Patient Screening
            </h1>
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              Intake heart sound (PCG) or echocardiogram (Echo) for automated AI risk triage & explainability
            </span>
          </div>
        </div>
      </div>

      {/* Clinical Presets / Demo Patient Bar */}
      <div
        className="card"
        style={{
          padding: '16px 20px',
          marginBottom: '24px',
          background: 'hsla(221, 100%, 55%, 0.04)',
          borderColor: 'hsla(221, 100%, 55%, 0.25)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={16} color="var(--brand-primary)" />
            <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--brand-primary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              One-Click Clinical Test Presets (Real CirCor & EchoNet Data)
            </span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Click any patient to test immediate workflow
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px' }}>
          {demoSamples.map((sample) => {
            const isSelected = selectedDemoId === sample.sample_id;
            return (
              <button
                key={sample.sample_id}
                type="button"
                className={`btn btn-sm ${isSelected ? 'btn-primary' : 'btn-outline'}`}
                style={{
                  textAlign: 'left',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-md)',
                  height: 'auto',
                  borderWidth: isSelected ? '2px' : '1px',
                }}
                onClick={() => handleSelectDemo(sample)}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', marginBottom: '4px' }}>
                  <span style={{ fontWeight: '700', fontSize: '13px' }}>{sample.patient_name}</span>
                  <span
                    style={{
                      fontSize: '10px',
                      fontWeight: '800',
                      padding: '2px 6px',
                      borderRadius: 'var(--radius-full)',
                      background: isSelected ? 'rgba(255,255,255,0.25)' : 'var(--bg-elevated)',
                    }}
                  >
                    {sample.modality}
                  </span>
                </div>
                <span style={{ fontSize: '11px', opacity: 0.85 }}>
                  {sample.expected_type} • {sample.age_group}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Screening Intake Form */}
      <form onSubmit={handleSubmit} className="card" style={{ padding: 'var(--sp-8)' }}>
        {errorMessage && (
          <div
            style={{
              padding: '12px 16px',
              borderRadius: 'var(--radius-md)',
              background: 'hsla(0, 84%, 60%, 0.1)',
              border: '1px solid hsla(0, 84%, 60%, 0.3)',
              color: 'hsl(0, 75%, 45%)',
              fontSize: '13px',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '20px',
            }}
          >
            <AlertCircle size={18} />
            {errorMessage}
          </div>
        )}

        {/* Patient Demographics */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginBottom: '24px' }}>
          <div>
            <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '6px' }}>
              <span>Patient Identifier *</span>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={generateRandomPatientId}
                style={{ fontSize: '11px', padding: '0 4px', color: 'var(--brand-primary)', height: 'auto' }}
              >
                <RefreshCw size={11} style={{ marginRight: '3px' }} /> Auto-ID
              </button>
            </label>
            <input
              type="text"
              className="input"
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              placeholder="e.g. P-4029"
              required
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '6px' }}>
              Patient Full Name *
            </label>
            <input
              type="text"
              className="input"
              value={patientName}
              onChange={(e) => setPatientName(e.target.value)}
              placeholder="e.g. Liam Davis"
              required
              style={{ width: '100%' }}
            />
          </div>
        </div>

        {/* Age Group & Modality Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px', marginBottom: '24px' }}>
          {/* Age Group */}
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '8px' }}>
              Pediatric Age Group
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
              {AGE_GROUPS.map((ag) => (
                <button
                  key={ag.id}
                  type="button"
                  className={`btn btn-sm ${ageGroup === ag.id ? 'btn-primary' : 'btn-outline'}`}
                  style={{
                    padding: '8px 10px',
                    fontSize: '12px',
                    fontWeight: '700',
                    justifyContent: 'center',
                    borderWidth: ageGroup === ag.id ? '2px' : '1px',
                  }}
                  onClick={() => setAgeGroup(ag.id)}
                >
                  {ag.label}
                </button>
              ))}
            </div>
            {ageGroup === 'Neonate' && (
              <span style={{ display: 'block', marginTop: '6px', fontSize: '11px', color: 'hsl(35, 95%, 42%)' }}>
                ⚠️ Neonate: Elevated heart rate baseline and benign murmurs require extra care.
              </span>
            )}
          </div>

          {/* Diagnostic Modality */}
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '8px' }}>
              Screening Modality
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <button
                type="button"
                className={`btn ${modality === 'PCG' ? 'btn-primary' : 'btn-outline'}`}
                style={{
                  padding: '12px',
                  fontSize: '13px',
                  fontWeight: '700',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  borderWidth: modality === 'PCG' ? '2px' : '1px',
                }}
                onClick={() => {
                  setModality('PCG');
                  setSelectedFile(null);
                  setPreviewAudioUrl(null);
                }}
              >
                <Heart size={16} />
                PCG Heart Sound (.wav)
              </button>

              <button
                type="button"
                className={`btn ${modality === 'Echo' ? 'btn-primary' : 'btn-outline'}`}
                style={{
                  padding: '12px',
                  fontSize: '13px',
                  fontWeight: '700',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  borderWidth: modality === 'Echo' ? '2px' : '1px',
                }}
                onClick={() => {
                  setModality('Echo');
                  setSelectedFile(null);
                  setPreviewAudioUrl(null);
                }}
              >
                <Activity size={16} />
                Echo Video (.avi)
              </button>
            </div>
          </div>
        </div>

        {/* Drag & Drop File Zone */}
        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '8px' }}>
            Upload Diagnostic File ({modality === 'PCG' ? '.wav' : '.avi'})
          </label>

          <input
            type="file"
            ref={fileInputRef}
            accept={modality === 'PCG' ? '.wav,audio/wav' : '.avi,video/x-msvideo'}
            style={{ display: 'none' }}
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFileChange(e.target.files[0]);
              }
            }}
          />

          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current && fileInputRef.current.click()}
            style={{
              padding: '36px 20px',
              borderRadius: 'var(--radius-lg)',
              border: `2px dashed ${isDragOver ? 'var(--brand-primary)' : 'var(--border-strong)'}`,
              background: isDragOver
                ? 'hsla(221, 100%, 55%, 0.08)'
                : selectedFile
                ? 'hsla(142, 70%, 97%, 0.6)'
                : 'hsl(210, 20%, 98%)',
              textAlign: 'center',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
            }}
          >
            {selectedFile ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                <CheckCircle size={36} color="var(--brand-success)" />
                <span style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)' }}>
                  {selectedFile.name}
                </span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  {(selectedFile.size / 1024).toFixed(1)} KB • Click to choose a different file
                </span>
              </div>
            ) : selectedDemoId ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={36} color="var(--brand-primary)" />
                <span style={{ fontSize: '15px', fontWeight: '700', color: 'var(--brand-primary)' }}>
                  Clinical Preset Loaded: {demoSamples.find((d) => d.sample_id === selectedDemoId)?.name}
                </span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Using authentic dataset benchmark media • Click to upload custom file instead
                </span>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
                <div
                  style={{
                    width: '54px',
                    height: '54px',
                    borderRadius: '50%',
                    background: 'hsla(221, 100%, 55%, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--brand-primary)',
                  }}
                >
                  <UploadCloud size={28} />
                </div>
                <div>
                  <span style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)' }}>
                    Drag & Drop {modality === 'PCG' ? 'PCG .wav audio' : 'Echo .avi video'} here
                  </span>
                  <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>
                    or click to browse local files
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Inline Audio Preview Player if .wav selected */}
          {previewAudioUrl && (
            <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)' }}>
                Pre-upload sound check:
              </span>
              <audio src={previewAudioUrl} controls style={{ height: '36px', flex: 1 }} />
            </div>
          )}
        </div>

        {/* Technician Notes (Optional) */}
        <div style={{ marginBottom: '28px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '6px' }}>
            Technician Notes & Auscultation Position (Optional)
          </label>
          <textarea
            className="input"
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. Auscultated over mitral valve (apex) in supine position. Resting heart rate 115 bpm."
            style={{ width: '100%', resize: 'vertical' }}
          />
        </div>

        {/* Action Button */}
        <button
          type="submit"
          className="btn btn-primary w-full"
          disabled={isSubmitting}
          style={{
            padding: '13px 24px',
            fontSize: '15px',
            fontWeight: '600',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--brand-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px',
          }}
        >
          {isSubmitting ? (
            <>
              <RefreshCw size={20} className="animate-spin" />
              <span>Analyzing Screening Signal (Step {submitStep}/3)...</span>
            </>
          ) : (
            <>
              <span>🔍 Run AI Diagnostic Screening</span>
              <ArrowRight size={18} />
            </>
          )}
        </button>

        {/* Animated Step Tracker while submitting */}
        {isSubmitting && (
          <div style={{ marginTop: '18px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--brand-primary)', textAlign: 'center' }}>
              {submitStep === 1 && 'Extracting acoustic / video tensors & normalizing sampling rate...'}
              {submitStep === 2 && 'Evaluating PCGNet deep features & clinical flags...'}
              {submitStep === 3 && 'Computing spatio-temporal Grad-CAM explainability saliency...'}
              {submitStep === 4 && 'Screening report generated! Redirecting to triage view...'}
            </div>
          </div>
        )}
      </form>
    </div>
  );
}
