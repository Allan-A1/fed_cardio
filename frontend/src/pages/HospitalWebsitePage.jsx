import React, { useState } from 'react';
import {
  HeartPulse,
  Stethoscope,
  ShieldCheck,
  Building2,
  Calendar,
  Phone,
  MapPin,
  Clock,
  ArrowRight,
  ChevronRight,
  Award,
  FileText,
  CheckCircle2,
  Users,
  Lock,
  Activity,
  Sparkles,
  Search,
  ExternalLink,
  ChevronDown,
  Mail,
  AlertCircle
} from 'lucide-react';

export default function HospitalWebsitePage({ onGoToPortal }) {
  const [referralForm, setReferralForm] = useState({
    referringPhysician: '',
    institution: '',
    patientAgeMonths: '',
    priorityTier: 'elective',
    modality: 'multimodal',
    clinicalNotes: ''
  });
  const [formSubmitted, setFormSubmitted] = useState(false);
  const [activeSpecialty, setActiveSpecialty] = useState(0);

  const clinicalPrograms = [
    {
      id: 'fetal',
      title: 'Division of Fetal & Neonatal Cardiology',
      subtitle: 'In-utero diagnosis, hemodynamic counseling, and prenatal cardiac delivery planning.',
      focus: 'Critical Coarctation, HLHS & Complete Transposition',
      stats: '1,420+ Fetal Echocardiograms / yr',
      description: 'Our fetal cardiology service partners directly with high-risk maternal-fetal medicine specialists. Using advanced 4D high-resolution fetal echocardiography and fetal PCG Doppler acoustic analysis, congenital structural anomalies are mapped as early as 14 weeks gestation.'
    },
    {
      id: 'interventional',
      title: 'Pediatric Interventional Catheterization & EP',
      subtitle: 'Minimally invasive intracardiac structural repair and complex arrhythmia ablation.',
      focus: 'ASD/VSD Percutaneous Occlusion & Electrophysiology Mapping',
      stats: '99.1% Technical Success Rate',
      description: 'Equipped with biplane pediatric fluoroscopy and low-radiation 3D electro-anatomical mapping, our interventional suites perform device closures, balloon valvuloplasties, and pediatric radiofrequency ablations with reduced procedural downtime.'
    },
    {
      id: 'surgery',
      title: 'Congenital Cardiothoracic Surgery',
      subtitle: 'Comprehensive neonate and infant surgical repair for complex cyanotic malformations.',
      focus: 'Tetralogy of Fallot, Truncus Arteriosus & Norwood Reconstructions',
      stats: 'STS Registry 3-Star Quality Rating',
      description: 'Led by internationally recognized academic pediatric cardiothoracic surgeons, our surgical team operates within dedicated pediatric cardiac operating rooms utilizing biocompatible cardiopulmonary bypass systems tailored for neonates under 2.5 kilograms.'
    },
    {
      id: 'cicu',
      title: 'Pediatric Cardiac Intensive Care (CICU)',
      subtitle: 'Quaternary 24-bed specialized unit with continuous bedside hemodynamic telemetry.',
      focus: 'Post-Operative Inotropic Titration & ECMO Life Support',
      stats: '24/7 Board-Certified In-House Intensivists',
      description: 'Every bed in our dedicated Pediatric Cardiac Intensive Care Unit features continuous multi-lead vectorcardiography, non-invasive cerebral and renal near-infrared spectroscopy (NIRS), and federated predictive alerting for acute hemodynamic decompensation.'
    }
  ];

  const consortiumHospitals = [
    { name: "Apollo Children's Heart Center", role: "Primary Consortium Teaching Node", location: "Chennai / Hyderabad", status: "Active Node", screenings: "4,820" },
    { name: "Boston Pediatric Heart Pavilion", role: "Academic Affiliate Center", location: "Boston, MA", status: "Active Node", screenings: "3,140" },
    { name: "Great Ormond Pediatric Center", role: "European Research Partner", location: "London, UK", status: "Active Node", screenings: "2,650" },
    { name: "Lucile Packard Cardiology Group", role: "Co-Operative Clinical Node", location: "Stanford, CA", status: "Active Node", screenings: "2,190" },
    { name: "St. Jude Children's Heart Consortium", role: "Central Hub & Coordinating Node", location: "Memphis, TN", status: "Federation Hub", screenings: "1,480" }
  ];

  function handleSubmitReferral(e) {
    e.preventDefault();
    setFormSubmitted(true);
  }

  return (
    <div className="hospital-site">
      {/* ── TOP UTILITY STRIP (Institutional Credentials) ────────────────────── */}
      <div className="site-utility-bar">
        <div className="site-container utility-inner">
          <div className="utility-left">
            <span className="utility-badge">ACCREDITED TERTIARY PEDIATRIC CARDIOLOGY CONSORTIUM</span>
            <span className="utility-divider">|</span>
            <span className="utility-text">Emergency Clinical Transport: <strong>+1 (800) 555-HEART</strong></span>
          </div>
          <div className="utility-right">
            <span className="utility-text">IRB-Approved Federated AI Protocol #2026-CHD</span>
            <span className="utility-divider">|</span>
            <button
              onClick={onGoToPortal}
              className="utility-login-btn"
              id="utility-portal-btn"
            >
              <Lock size={12} />
              <span>Clinician & Node Gateway</span>
            </button>
          </div>
        </div>
      </div>

      {/* ── INSTITUTIONAL MASTHEAD NAVIGATION ─────────────────────────── */}
      <header className="site-masthead">
        <div className="site-container masthead-inner">
          <div className="site-brand">
            <div className="site-crest">
              <HeartPulse size={24} strokeWidth={2.2} />
            </div>
            <div className="site-brand-text">
              <span className="brand-institution">ST. JUDE & ST. LUKE PEDIATRIC HEART INSTITUTE</span>
              <span className="brand-department">Department of Pediatric Cardiology & Congenital Triage</span>
            </div>
          </div>

          <nav className="site-nav">
            <a href="#overview" className="site-nav-link">Institute</a>
            <a href="#programs" className="site-nav-link">Clinical Programs</a>
            <a href="#technology" className="site-nav-link">Screening Technology</a>
            <a href="#faculty" className="site-nav-link">Medical Faculty</a>
            <a href="#consortium" className="site-nav-link">Federated Network</a>
            <a href="#referral" className="site-nav-link">Physician Referral</a>
          </nav>

          <div className="masthead-actions">
            <button
              onClick={onGoToPortal}
              className="btn btn-primary site-gateway-btn"
              id="masthead-gateway-btn"
            >
              <Activity size={15} />
              <span>Launch Clinical Portal</span>
            </button>
          </div>
        </div>
      </header>

      {/* ── HERO EDITORIAL SECTION ───────────────────────────────────── */}
      <section id="overview" className="hero-editorial-section">
        <div className="site-container">
          <div className="hero-grid">
            <div className="hero-editorial-content">
              <div className="editorial-eyebrow">
                <span className="eyebrow-line"></span>
                <span>FEDERATED CLINICAL EXCELLENCE IN PEDIATRIC CARDIOLOGY</span>
              </div>
              <h1 className="hero-editorial-title">
                Specialized diagnosis and collaborative care for complex pediatric heart conditions.
              </h1>
              <p className="hero-editorial-lead">
                The St. Jude & St. Luke Pediatric Heart Institute unifies board-certified pediatric cardiologists, cardiothoracic surgeons, and academic research teaching hospitals. Through multi-institutional federated machine learning, our clinical gateway analyzes acoustic phonocardiogram auscultations and echocardiogram telemetry on-premises—ensuring strict patient privacy while elevating diagnostic accuracy across neonatal and pediatric populations.
              </p>

              <div className="hero-actions">
                <a href="#referral" className="btn btn-primary hero-btn-main">
                  <span>Refer a Pediatric Patient</span>
                  <ArrowRight size={15} />
                </a>
                <button onClick={onGoToPortal} className="btn btn-secondary hero-btn-sub">
                  <ShieldCheck size={16} />
                  <span>Hospital Node Triage Gateway</span>
                </button>
              </div>

              {/* Verified Institutional Performance Metrics */}
              <div className="hero-metrics-strip">
                <div className="metric-cell">
                  <span className="metric-val">14,280+</span>
                  <span className="metric-label">Pediatric Screenings Completed</span>
                </div>
                <div className="metric-cell">
                  <span className="metric-val">98.4%</span>
                  <span className="metric-label">Dual-Modality Sensitivity</span>
                </div>
                <div className="metric-cell">
                  <span className="metric-val">6</span>
                  <span className="metric-label">Academic Consortium Hospitals</span>
                </div>
                <div className="metric-cell">
                  <span className="metric-val">0 kB</span>
                  <span className="metric-label">Raw Patient Data Egress (100% On-Prem)</span>
                </div>
              </div>
            </div>

            <div className="hero-media-wrapper">
              <div className="hero-frame">
                <img
                  src="/images/clinic-exam.jpg"
                  alt="Pediatric cardiology clinical examination suite with echocardiography system"
                  className="hero-image"
                />
                <div className="hero-caption">
                  <div className="caption-tag">Clinical Suite 4B</div>
                  <div className="caption-text">
                    Pediatric echocardiography and hemodynamic Doppler examination conducted by staff pediatric cardiologists at St. Luke’s Heart Pavilion.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── CLINICAL PROGRAMS & DIVISIONS (Varied Editorial Composition) ── */}
      <section id="programs" className="section-clinical-programs">
        <div className="site-container">
          <div className="section-header-editorial">
            <span className="section-kicker">COMPREHENSIVE CLINICAL DIVISIONS</span>
            <h2 className="section-heading">
              Dedicated subspecialty services across the continuum of congenital heart disease.
            </h2>
            <p className="section-subheading">
              From early in-utero fetal echocardiographic screening through complex adolescent catheterization and adulthood congenital transitions, our multidisciplinary teams deliver patient-centered care guided by clinical evidence.
            </p>
          </div>

          <div className="programs-layout">
            {/* Interactive Program Selector */}
            <div className="programs-nav-col">
              {clinicalPrograms.map((program, idx) => (
                <div
                  key={program.id}
                  onClick={() => setActiveSpecialty(idx)}
                  className={`program-nav-item ${activeSpecialty === idx ? 'active' : ''}`}
                >
                  <div className="nav-item-num">0{idx + 1}</div>
                  <div className="nav-item-content">
                    <div className="nav-item-title">{program.title}</div>
                    <div className="nav-item-sub">{program.focus}</div>
                  </div>
                  <ChevronRight size={16} className="nav-item-arrow" />
                </div>
              ))}
            </div>

            {/* Program Detail Editorial Card */}
            <div className="program-display-col">
              <div className="program-editorial-card">
                <div className="program-card-header">
                  <div className="program-badge">Specialty Division {activeSpecialty + 1} of {clinicalPrograms.length}</div>
                  <span className="program-metric">{clinicalPrograms[activeSpecialty].stats}</span>
                </div>

                <h3 className="program-card-title">{clinicalPrograms[activeSpecialty].title}</h3>
                <p className="program-card-sub">{clinicalPrograms[activeSpecialty].subtitle}</p>

                <div className="program-divider"></div>

                <p className="program-card-body">
                  {clinicalPrograms[activeSpecialty].description}
                </p>

                <div className="program-scope-box">
                  <div className="scope-header">Primary Clinical Focus & Surgical Indications</div>
                  <div className="scope-items">
                    <div className="scope-item">
                      <CheckCircle2 size={16} className="scope-icon" />
                      <span>{clinicalPrograms[activeSpecialty].focus}</span>
                    </div>
                    <div className="scope-item">
                      <CheckCircle2 size={16} className="scope-icon" />
                      <span>Multidisciplinary weekly surgical and catheterization conference review</span>
                    </div>
                    <div className="scope-item">
                      <CheckCircle2 size={16} className="scope-icon" />
                      <span>Integrated with on-premises FedMed acoustic screening telemetry</span>
                    </div>
                  </div>
                </div>

                <div className="program-card-footer">
                  <a href="#referral" className="btn btn-secondary btn-sm">
                    <span>Submit Departmental Referral</span>
                    <ArrowRight size={13} />
                  </a>
                  <span className="program-card-contact">Inquiries: <strong>pediatrics@heart.fedmed.org</strong></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── ARCHITECTURAL CAMPUS PREVIEW ─────────────────────────────── */}
      <section className="section-campus-feature">
        <div className="site-container">
          <div className="campus-grid">
            <div className="campus-image-frame">
              <img
                src="/images/institute-exterior.jpg"
                alt="St. Luke's Pediatric Heart Institute Pavilion Exterior Architecture"
                className="campus-image"
              />
            </div>
            <div className="campus-content">
              <span className="section-kicker">PHYSICAL & CLINICAL INFRASTRUCTURE</span>
              <h2 className="section-heading">Designed for clinical composure, family comfort, and medical precision.</h2>
              <p className="campus-text">
                The St. Luke’s Heart Pavilion was commissioned with a singular mandate: to eliminate the sterile, anxiety-inducing atmosphere typical of acute medical facilities while preserving the highest aseptic standards required for quaternary congenital heart surgery.
              </p>
              <div className="campus-specs">
                <div className="spec-row">
                  <span className="spec-name">Dedicated Pediatric Operating Rooms</span>
                  <span className="spec-value">4 Integrated Hybrid Suites</span>
                </div>
                <div className="spec-row">
                  <span className="spec-name">Pediatric Catheterization Laboratories</span>
                  <span className="spec-value">2 Biplane Low-Dose Fluoroscopy Units</span>
                </div>
                <div className="spec-row">
                  <span className="spec-name">Outpatient Echocardiography Suites</span>
                  <span className="spec-value">8 Sound-Attenuated Diagnostic Rooms</span>
                </div>
                <div className="spec-row">
                  <span className="spec-name">Institutional Accreditation</span>
                  <span className="spec-value">Joint Commission & STS 3-Star Center</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── FEDERATED SCREENING TECHNOLOGY ARCHITECTURE ────────────────── */}
      <section id="technology" className="section-technology">
        <div className="site-container">
          <div className="section-header-editorial">
            <span className="section-kicker">FEDERATED DIAGNOSTIC INTELLIGENCE</span>
            <h2 className="section-heading">
              Privacy-preserving federated screening for pediatric congenital heart disease.
            </h2>
            <p className="section-subheading">
              Unlike traditional cloud machine learning architectures that require transmitting sensitive patient recordings to third-party servers, FedMed executes all feature extraction directly inside hospital firewalls.
            </p>
          </div>

          <div className="technology-trio">
            {/* Column 1 */}
            <div className="tech-col-card">
              <div className="tech-badge">MODALITY I</div>
              <h3 className="tech-card-title">Phonocardiogram (PCG) Acoustic Auscultation</h3>
              <p className="tech-card-text">
                Electronic stethoscopic recordings are captured at standard aortic, pulmonic, tricuspid, and mitral auscultation sites. Continuous audio waveforms are segmented into discrete S1/systole/S2/diastole intervals to detect turbulent murmurs indicative of VSD, ASD, or Tetralogy of Fallot.
              </p>
              <ul className="tech-feature-list">
                <li>High-order Butterworth bandpass filtering (25–400 Hz)</li>
                <li>Wavelet spectrogram transform for acoustic feature mapping</li>
                <li>Grad-CAM visual attribution highlighting murmur windows</li>
              </ul>
            </div>

            {/* Column 2 */}
            <div className="tech-col-card">
              <div className="tech-badge">MODALITY II</div>
              <h3 className="tech-card-title">Transthoracic Echocardiogram (Echo) Biometrics</h3>
              <p className="tech-card-text">
                Cross-sectional ultrasound measurements evaluate left ventricular systolic function. Automatically parses ventricular ejection fraction (EF), end-diastolic volumes, and fractional shortening to validate hemodynamic compromise before invasive intervention.
              </p>
              <ul className="tech-feature-list">
                <li>Automated EF contractility indexing (≥ 55% normal baseline)</li>
                <li>End-systolic and end-diastolic chamber volumetric tracking</li>
                <li>Concordance cross-check against acoustic murmur findings</li>
              </ul>
            </div>

            {/* Column 3 */}
            <div className="tech-col-card tech-highlight">
              <div className="tech-badge tech-badge-primary">NETWORK GOVERNANCE</div>
              <h3 className="tech-card-title">Heterogeneous Federated Consensus (FedMed)</h3>
              <p className="tech-card-text">
                Participating medical nodes train local multi-modal models on their regional pediatric cohorts. Only anonymized model weight vectors are securely aggregated via FedAvg/FedProx algorithms on the central coordinator—zero patient identities ever leave the hospital premises.
              </p>
              <ul className="tech-feature-list">
                <li>Strict HIPAA Title II and EU GDPR compliant by mathematical design</li>
                <li>Continuous cluster personalization for hospital-specific demographics</li>
                <li>Cryptographic checksums verifying model weight integrity</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── SENIOR MEDICAL FACULTY & CLINICAL DIRECTORS ────────────────── */}
      <section id="faculty" className="section-faculty">
        <div className="site-container">
          <div className="section-header-editorial">
            <span className="section-kicker">ACADEMIC LEADERSHIP & SENIOR FACULTY</span>
            <h2 className="section-heading">Physicians and researchers devoted exclusively to young hearts.</h2>
            <p className="section-subheading">
              Our faculty members hold academic appointments at premier medical universities and lead international clinical trials establishing modern standards for congenital cardiac care.
            </p>
          </div>

          <div className="faculty-spotlight">
            <div className="faculty-director-card">
              <div className="director-image-frame">
                <img
                  src="/images/faculty-director.jpg"
                  alt="Dr. Eleanor Reed, MD, Chief of Pediatric Cardiology"
                  className="director-image"
                />
              </div>
              <div className="director-bio">
                <div className="director-badge">CHIEF OF PEDIATRIC CARDIOLOGY</div>
                <h3 className="director-name">Dr. Eleanor Reed, MD, FACC, FAAP</h3>
                <div className="director-creds">
                  Professor of Pediatric Medicine | Senior Clinical Investigator, FedMed Consortium
                </div>
                <p className="director-text">
                  Dr. Reed has dedicated over 24 years to pediatric cardiac auscultation and non-invasive hemodynamic imaging. A graduate of Johns Hopkins University School of Medicine and former fellow at Boston Children’s Hospital, her clinical research focuses on early neonatal murmur triage in community and rural hospital settings.
                </p>
                <div className="director-meta-grid">
                  <div className="meta-box">
                    <span className="meta-title">Board Certifications</span>
                    <span className="meta-val">Pediatric Cardiology & Adult Congenital Heart Disease</span>
                  </div>
                  <div className="meta-box">
                    <span className="meta-title">Academic Publications</span>
                    <span className="meta-val">84 Peer-Reviewed Papers (Circulation, JACC, NEJM)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Associate Leadership Cards */}
            <div className="faculty-grid">
              <div className="faculty-card">
                <div className="card-kicker">CARDIOTHORACIC SURGERY</div>
                <h4 className="faculty-card-name">Dr. Alistair Chen, MD, PhD, FACS</h4>
                <div className="faculty-card-role">Director of Pediatric Cardiothoracic Surgery</div>
                <p className="faculty-card-desc">
                  Specializes in complex neonatal aortic arch reconstructions, valve-sparing root procedures, and minimal-access pediatric sternotomies.
                </p>
                <div className="faculty-card-contact">Office: +1 (800) 555-4120</div>
              </div>

              <div className="faculty-card">
                <div className="card-kicker">ELECTROPHYSIOLOGY</div>
                <h4 className="faculty-card-name">Dr. Sarah Jenkins, MD, FHRS</h4>
                <div className="faculty-card-role">Director of Pediatric Arrhythmia & Pacemaker Service</div>
                <p className="faculty-card-desc">
                  Nationally recognized expert in pediatric supraventricular tachycardia catheter ablation and inherited channelopathies (Long QT syndrome).
                </p>
                <div className="faculty-card-contact">Office: +1 (800) 555-4122</div>
              </div>

              <div className="faculty-card">
                <div className="card-kicker">CRITICAL CARE (CICU)</div>
                <h4 className="faculty-card-name">Dr. Marcus Reynolds, MD</h4>
                <div className="faculty-card-role">Medical Director, Pediatric Cardiac Intensive Care</div>
                <p className="faculty-card-desc">
                  Leads our 24-bed specialized CICU, pioneering federated real-time early warning telemetry to predict post-operative low cardiac output syndrome.
                </p>
                <div className="faculty-card-contact">Office: +1 (800) 555-4125</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── FEDERATED HOSPITAL CONSORTIUM MEMBERS ────────────────────── */}
      <section id="consortium" className="section-consortium">
        <div className="site-container">
          <div className="section-header-editorial">
            <span className="section-kicker">MULTI-CENTER RESEARCH COLLABORATIVE</span>
            <h2 className="section-heading">Active teaching hospital nodes across the FedMed network.</h2>
            <p className="section-subheading">
              Participating hospitals deploy secure on-premises FedMed worker agents that evaluate clinical cohorts, update local gradient estimators, and coordinate with the global consensus server.
            </p>
          </div>

          <div className="consortium-table-wrapper">
            <table className="consortium-table">
              <thead>
                <tr>
                  <th>Participating Medical Center</th>
                  <th>Institutional Role</th>
                  <th>Regional Location</th>
                  <th>Total Screenings</th>
                  <th>Network Link</th>
                </tr>
              </thead>
              <tbody>
                {consortiumHospitals.map((hosp, idx) => (
                  <tr key={idx}>
                    <td>
                      <div className="hosp-name-cell">
                        <Building2 size={16} className="hosp-icon" />
                        <strong>{hosp.name}</strong>
                      </div>
                    </td>
                    <td>{hosp.role}</td>
                    <td>{hosp.location}</td>
                    <td><span className="tabular-num">{hosp.screenings}</span></td>
                    <td>
                      <span className="hosp-status-pill">
                        <span className="hosp-dot"></span>
                        {hosp.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── PHYSICIAN REFERRAL & INTAKE SECTION ──────────────────────── */}
      <section id="referral" className="section-referral">
        <div className="site-container">
          <div className="referral-grid">
            <div className="referral-info-col">
              <span className="section-kicker">PHYSICIAN CONSULTATION & REFERRALS</span>
              <h2 className="section-heading">Initiate an urgent triage or outpatient referral.</h2>
              <p className="referral-text">
                Referring pediatricians, family physicians, and community obstetricians can transfer clinical telemetry directly through the FedMed network or submit a consultation request.
              </p>

              <div className="referral-contacts">
                <div className="contact-item">
                  <Phone size={18} className="contact-icon" />
                  <div>
                    <div className="contact-label">24/7 Physician Transfer Hotline</div>
                    <div className="contact-val">+1 (800) 555-HEART / Ext. 901</div>
                  </div>
                </div>
                <div className="contact-item">
                  <Mail size={18} className="contact-icon" />
                  <div>
                    <div className="contact-label">Clinical Coordinator Intake</div>
                    <div className="contact-val">referrals@pediatric.fedmed.org</div>
                  </div>
                </div>
                <div className="contact-item">
                  <MapPin size={18} className="contact-icon" />
                  <div>
                    <div className="contact-label">Hospital Heart Pavilion Address</div>
                    <div className="contact-val">500 St. Jude Way, Pediatric Specialties Pavilion, Floor 4</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="referral-form-col">
              <div className="referral-card">
                <div className="referral-card-header">
                  <h3 className="referral-title">Physician Referral & Triage Request</h3>
                  <p className="referral-desc">Confidential clinical communication between licensed healthcare practitioners.</p>
                </div>

                {formSubmitted ? (
                  <div className="referral-success">
                    <CheckCircle2 size={40} className="success-icon" />
                    <h4>Referral Transmitted to Clinical Triage</h4>
                    <p>
                      The on-call pediatric cardiology fellow and intake coordinator have received your inquiry. For urgent cyanotic neonates, please also call the 24/7 transport hotline directly.
                    </p>
                    <button
                      onClick={() => setFormSubmitted(false)}
                      className="btn btn-secondary btn-sm"
                    >
                      Submit Another Referral
                    </button>
                  </div>
                ) : (
                  <form onSubmit={handleSubmitReferral} className="referral-form">
                    <div className="form-row">
                      <div className="form-group">
                        <label className="form-label">Referring Physician Name *</label>
                        <input
                          type="text"
                          required
                          placeholder="e.g. Dr. Arthur Miller, MD"
                          className="form-input"
                          value={referralForm.referringPhysician}
                          onChange={e => setReferralForm({ ...referralForm, referringPhysician: e.target.value })}
                        />
                      </div>
                      <div className="form-group">
                        <label className="form-label">Referring Hospital / Clinic *</label>
                        <input
                          type="text"
                          required
                          placeholder="e.g. St. Mary Regional Hospital"
                          className="form-input"
                          value={referralForm.institution}
                          onChange={e => setReferralForm({ ...referralForm, institution: e.target.value })}
                        />
                      </div>
                    </div>

                    <div className="form-row">
                      <div className="form-group">
                        <label className="form-label">Patient Age (Months / Years)</label>
                        <input
                          type="text"
                          placeholder="e.g. 8 months"
                          className="form-input"
                          value={referralForm.patientAgeMonths}
                          onChange={e => setReferralForm({ ...referralForm, patientAgeMonths: e.target.value })}
                        />
                      </div>
                      <div className="form-group">
                        <label className="form-label">Clinical Triage Priority *</label>
                        <select
                          className="form-input form-select"
                          value={referralForm.priorityTier}
                          onChange={e => setReferralForm({ ...referralForm, priorityTier: e.target.value })}
                        >
                          <option value="emergency">Emergency (Within 2 Hours - Transfer Hotline)</option>
                          <option value="urgent">Urgent Inpatient Triage (Within 24 Hours)</option>
                          <option value="elective">Elective Outpatient Consultation (Within 5 Days)</option>
                        </select>
                      </div>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Clinical Diagnostic Modality Needed</label>
                      <select
                        className="form-input form-select"
                        value={referralForm.modality}
                        onChange={e => setReferralForm({ ...referralForm, modality: e.target.value })}
                      >
                        <option value="multimodal">Combined PCG Auscultation & Transthoracic Echo</option>
                        <option value="fetal">Comprehensive Fetal Echocardiogram (Prenatal)</option>
                        <option value="ep">Pediatric Electrophysiology / Holter Review</option>
                        <option value="surgical">Post-Surgical Quaternary Second Opinion</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Clinical Findings & Suspected Defect</label>
                      <textarea
                        rows={3}
                        placeholder="Provide details on auscultation murmur grading (e.g., Grade III/VI harsh pansystolic murmur at LSB), peripheral oxygen saturation, or preliminary ultrasound notes..."
                        className="form-input form-textarea"
                        value={referralForm.clinicalNotes}
                        onChange={e => setReferralForm({ ...referralForm, clinicalNotes: e.target.value })}
                      ></textarea>
                    </div>

                    <div className="referral-form-footer">
                      <button type="submit" className="btn btn-primary" id="btn-submit-referral">
                        <span>Submit Confidential Referral</span>
                        <ArrowRight size={15} />
                      </button>
                      <span className="hipaa-note">
                        <Lock size={12} />
                        <span>Transmitted over 256-bit TLS encrypted HIPAA pathway</span>
                      </span>
                    </div>
                  </form>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── INSTITUTIONAL FOOTER ─────────────────────────────────────── */}
      <footer className="site-footer">
        <div className="site-container">
          <div className="footer-top-grid">
            <div className="footer-col-brand">
              <div className="footer-brand">
                <HeartPulse size={20} className="footer-crest" />
                <span className="footer-brand-title">St. Jude & St. Luke Pediatric Heart Institute</span>
              </div>
              <p className="footer-desc">
                An accredited tertiary pediatric cardiology academic institute and research coordinating center for the multi-institutional FedMed federated learning network. Dedicated to eliminating diagnostic disparities in congenital heart diseases worldwide.
              </p>
              <div className="footer-governance">
                <span>IRB Human Subjects Protocol #2026-CHD</span>
                <span>•</span>
                <span>HIPAA Title II Security Compliant</span>
              </div>
            </div>

            <div className="footer-col">
              <div className="footer-heading">Clinical Divisions</div>
              <ul className="footer-links">
                <li><a href="#programs">Fetal & Prenatal Cardiology</a></li>
                <li><a href="#programs">Pediatric Interventional Catheterization</a></li>
                <li><a href="#programs">Congenital Cardiothoracic Surgery</a></li>
                <li><a href="#programs">Cardiac Intensive Care Unit (CICU)</a></li>
                <li><a href="#programs">Adult Congenital Heart Disease (ACHD)</a></li>
              </ul>
            </div>

            <div className="footer-col">
              <div className="footer-heading">Consortium Portals</div>
              <ul className="footer-links">
                <li><button onClick={onGoToPortal} className="footer-link-btn">Hospital Node Login</button></li>
                <li><button onClick={onGoToPortal} className="footer-link-btn">Clinical Triage Workstation</button></li>
                <li><button onClick={onGoToPortal} className="footer-link-btn">Central Network Admin</button></li>
                <li><a href="#technology">Federated Learning Protocols</a></li>
                <li><a href="#consortium">Participating Academic Hospitals</a></li>
              </ul>
            </div>

            <div className="footer-col">
              <div className="footer-heading">Hospital Contact</div>
              <div className="footer-contact-block">
                <p><strong>Main Pavilion:</strong> 500 St. Jude Way, Memphis, TN</p>
                <p><strong>Emergency Transport:</strong> +1 (800) 555-HEART</p>
                <p><strong>Physician Referral Desk:</strong> +1 (800) 555-4100</p>
                <p><strong>Clinical Email:</strong> contact@heart.fedmed.org</p>
              </div>
            </div>
          </div>

          <div className="footer-bottom-strip">
            <div className="footer-copy">
              © 2026 St. Jude & St. Luke Pediatric Heart Institute. FedMed Heterogeneous Federated Consensus Consortium. All rights reserved.
            </div>
            <div className="footer-legal">
              <a href="#">Privacy Policy</a>
              <span>•</span>
              <a href="#">Notice of Privacy Practices (HIPAA)</a>
              <span>•</span>
              <a href="#">Clinical Terms of Access</a>
              <span>•</span>
              <button onClick={onGoToPortal} className="footer-staff-link">Staff Login</button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
