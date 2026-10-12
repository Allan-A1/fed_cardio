import React, { useState } from 'react';
import { AlertCircle, CheckCircle2, Send, ShieldAlert, FileText, Check, Clock } from 'lucide-react';
import { Modal } from './UI';

export default function DecisionPanel({
  reportId,
  currentStatus = 'pending',
  doctorNotes,
  technicianNotes,
  onEscalate,
  onDismiss,
}) {
  const [escalateModalOpen, setEscalateModalOpen] = useState(false);
  const [dismissModalOpen, setDismissModalOpen] = useState(false);
  const [notes, setNotes] = useState('');
  const [urgency, setUrgency] = useState('Urgent (< 4h)');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isEscalated = currentStatus === 'escalated';
  const isDismissed = currentStatus === 'dismissed';

  const handleEscalateSubmit = async () => {
    setIsSubmitting(true);
    try {
      await onEscalate({
        doctor_notes: `[Priority: ${urgency}] ${notes}`,
        technician_notes: notes,
      });
      setEscalateModalOpen(false);
      setNotes('');
    } catch (e) {
      console.error(e);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDismissSubmit = async () => {
    setIsSubmitting(true);
    try {
      await onDismiss({
        technician_notes: notes || 'Technician verified normal baseline. No doctor review requested.',
      });
      setDismissModalOpen(false);
      setNotes('');
    } catch (e) {
      console.error(e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="card"
      style={{
        padding: 'var(--sp-6)',
        background: 'var(--bg-surface)',
        borderColor: isEscalated
          ? 'hsla(0, 84%, 60%, 0.4)'
          : isDismissed
          ? 'hsla(142, 70%, 42%, 0.4)'
          : 'var(--border-default)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <h4 style={{ fontSize: '16px', fontWeight: '800', color: 'var(--text-primary)', margin: 0 }}>
            Technician Clinical Decision & Triage Action
          </h4>
          <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Review AI findings and determine clinical pathway for this patient
          </span>
        </div>

        {/* Current status pill */}
        <div>
          {isEscalated && (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 14px',
                borderRadius: 'var(--radius-full)',
                background: 'hsla(0, 84%, 60%, 0.12)',
                color: 'hsl(0, 75%, 45%)',
                fontWeight: '700',
                fontSize: '12px',
                border: '1px solid hsla(0, 84%, 60%, 0.3)',
              }}
            >
              <ShieldAlert size={15} />
              Escalated to Attending Doctor
            </span>
          )}
          {isDismissed && (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 14px',
                borderRadius: 'var(--radius-full)',
                background: 'hsla(142, 70%, 42%, 0.12)',
                color: 'hsl(142, 70%, 30%)',
                fontWeight: '700',
                fontSize: '12px',
                border: '1px solid hsla(142, 70%, 42%, 0.3)',
              }}
            >
              <CheckCircle2 size={15} />
              Marked Normal — No Action
            </span>
          )}
          {!isEscalated && !isDismissed && (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 14px',
                borderRadius: 'var(--radius-full)',
                background: 'hsla(35, 95%, 52%, 0.12)',
                color: 'hsl(35, 95%, 40%)',
                fontWeight: '700',
                fontSize: '12px',
                border: '1px solid hsla(35, 95%, 52%, 0.3)',
              }}
            >
              <Clock size={15} />
              Pending Technician Triage
            </span>
          )}
        </div>
      </div>

      {/* Decision CTA Buttons */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '16px',
          marginTop: '8px',
          marginBottom: '18px',
        }}
      >
        <button
          className="btn btn-outline"
          onClick={() => setDismissModalOpen(true)}
          style={{
            padding: '16px 20px',
            borderRadius: 'var(--radius-md)',
            borderColor: 'var(--brand-success)',
            color: 'hsl(142, 70%, 32%)',
            background: 'hsla(142, 70%, 97%, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px',
            fontSize: '15px',
            fontWeight: '700',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <CheckCircle2 size={20} color="var(--brand-success)" />
          Mark Normal — No Action Needed
        </button>

        <button
          className="btn btn-danger"
          onClick={() => setEscalateModalOpen(true)}
          style={{
            padding: '12px 20px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--brand-danger)',
            color: '#FFFFFF',
            border: '1px solid var(--brand-danger)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            fontSize: '14px',
            fontWeight: '600',
          }}
        >
          <Send size={16} />
          Escalate to Pediatric Cardiologist
        </button>
      </div>

      {/* Existing Notes display if present */}
      {(doctorNotes || technicianNotes) && (
        <div
          style={{
            padding: '14px 16px',
            background: 'var(--bg-elevated)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            marginBottom: '16px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <FileText size={16} color="var(--text-secondary)" />
            <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)' }}>
              Clinical Triage Audit Notes:
            </span>
          </div>
          {technicianNotes && (
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: '0 0 6px' }}>
              <strong>Technician Note:</strong> {technicianNotes}
            </p>
          )}
          {doctorNotes && (
            <p style={{ fontSize: '13px', color: 'hsl(0, 75%, 45%)', margin: 0 }}>
              <strong>Cardiology Instructions:</strong> {doctorNotes}
            </p>
          )}
        </div>
      )}

      {/* Medical Disclaimer Banner */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: '10px',
          padding: '12px 14px',
          background: 'var(--bg-base)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-subtle)',
          fontSize: '12px',
          color: 'var(--text-muted)',
          lineHeight: '1.5',
        }}
      >
        <AlertCircle size={16} style={{ flexShrink: 0, marginTop: '2px', color: 'var(--text-muted)' }} />
        <span>
          <strong>Clinical Decision Support Disclaimer:</strong> FedMed AI screening outputs are probabilistic assistive signals designed to augment lab triage workflows. This report does not replace certified pediatric clinical auscultation or comprehensive echocardiographic diagnosis.
        </span>
      </div>

      {/* Escalation Modal */}
      <Modal
        open={escalateModalOpen}
        onClose={() => setEscalateModalOpen(false)}
        title="Escalate Screening Report to Physician"
        id="modal-escalate"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '6px' }}>
              Escalation Priority Level
            </label>
            <div style={{ display: 'flex', gap: '10px' }}>
              {['Routine (24h)', 'Urgent (< 4h)', 'STAT Emergency'].map((lvl) => (
                <button
                  key={lvl}
                  type="button"
                  className={`btn btn-sm ${urgency === lvl ? 'btn-danger' : 'btn-outline'}`}
                  onClick={() => setUrgency(lvl)}
                  style={{ flex: 1, padding: '8px' }}
                >
                  {lvl}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '6px' }}>
              Clinical Findings / Stethoscope Auscultation Notes
            </label>
            <textarea
              className="input"
              rows={4}
              placeholder="e.g., Systolic blowing murmur audible over apex. XAI highlights high-energy focus at 2.1s–3.4s. Advise direct cardiology auscultation or follow-up echo..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              style={{ width: '100%', resize: 'vertical' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
            <button className="btn btn-ghost" onClick={() => setEscalateModalOpen(false)} disabled={isSubmitting}>
              Cancel
            </button>
            <button className="btn btn-danger" onClick={handleEscalateSubmit} disabled={isSubmitting}>
              {isSubmitting ? 'Submitting...' : 'Confirm Escalation'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Dismiss Modal */}
      <Modal
        open={dismissModalOpen}
        onClose={() => setDismissModalOpen(false)}
        title="Confirm Normal Auscultation / Dismiss Triage"
        id="modal-dismiss"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: 0 }}>
            Mark this patient's screening as Normal. The record will be updated in the registry as routine observation with no doctor consultation required.
          </p>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '6px' }}>
              Technician Verification Note (Optional)
            </label>
            <textarea
              className="input"
              rows={3}
              placeholder="e.g., Clean S1/S2 heart sounds, physiological baseline verified, no adventitious murmurs..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              style={{ width: '100%', resize: 'vertical' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
            <button className="btn btn-ghost" onClick={() => setDismissModalOpen(false)} disabled={isSubmitting}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleDismissSubmit} disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : 'Confirm Normal Baseline'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
