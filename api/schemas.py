"""
Pydantic schemas for all API responses.
"""
from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel


# ── Hospital ──────────────────────────────────────────────────────────────────

class HospitalOut(BaseModel):
    id: str
    name: str
    city: str
    country: str
    status: str
    joinedDate: str
    contributionScore: int
    patientsContributed: int
    roundsParticipated: int
    initials: str


# ── Auth & Admin ──────────────────────────────────────────────────────────────

class AuthLoginRequest(BaseModel):
    role: str   # 'admin' | 'hospital' | 'technician'
    hospital_id: Optional[str] = None
    access_key: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    tech_id: Optional[str] = None
    pin: Optional[str] = None


class AuthLoginResponse(BaseModel):
    ok: bool
    token: str
    user: dict
    message: Optional[str] = None


class HospitalCreateRequest(BaseModel):
    name: str
    city: str
    country: str = "India"
    contact_email: str
    authorized_modalities: List[str] = ["PCG", "ECG", "Echo"]
    notes: Optional[str] = ""
    status: str = "active"


class HospitalStatusUpdateRequest(BaseModel):
    status: str   # 'active' | 'suspended' | 'pending'


class HospitalRecordOut(BaseModel):
    id: str
    name: str
    city: str
    country: str
    contact_email: str
    access_key: str
    status: str
    authorized_modalities: List[str]
    joined_clusters: List[str]
    contribution_score: float
    patients_contributed: int
    rounds_participated: int
    initials: str
    created_at: str
    notes: Optional[str] = ""


class AdminMetricsOut(BaseModel):
    total_hospitals: int
    active_hospitals: int
    total_technicians: int
    total_cluster_nodes: int
    total_patients_contributed: int
    total_rounds_participated: int
    average_contribution_score: float


class TechnicianOut(BaseModel):
    tech_id: str
    hospital_id: str
    hospital_name: Optional[str] = None
    name: str
    pin: str
    role_title: str
    status: str
    created_at: str


# ── Cluster ───────────────────────────────────────────────────────────────────

class ClusterOut(BaseModel):
    id: str
    name: str
    description: str
    modality: str
    icon: str
    color: str
    colorGlass: str
    borderColor: str
    hospitals: int
    currentRound: int
    totalRounds: int
    globalAccuracy: float
    prevAccuracy: float
    status: str          # training | active | idle
    joined: bool
    datasetPath: str
    localAccuracy: Optional[float]
    localSamples: int
    tags: List[str]
    lastSync: str


# ── Training ──────────────────────────────────────────────────────────────────

class TrainingStatusOut(BaseModel):
    isRunning: bool
    currentRound: int
    localEpoch: int
    localAcc: float
    clusterId: Optional[str]
    pid: Optional[int]


class LogLine(BaseModel):
    time: str
    msg: str
    type: str   # info | success | warning | error


class TrainingLogsOut(BaseModel):
    logs: List[LogLine]


# ── Metrics history ───────────────────────────────────────────────────────────

class MetricPoint(BaseModel):
    round: int
    global_: float
    local: Optional[float]

    class Config:
        populate_by_name = True


class AccuracyHistoryOut(BaseModel):
    history: List[dict]   # [{round, global, local}]


# ── Results ───────────────────────────────────────────────────────────────────

class ResultOut(BaseModel):
    hospital: str
    modality: str
    dataset: str
    model: str
    n_train: int
    n_val: int
    n_test: int
    test_loss: Optional[float] = None
    test_acc: Optional[float] = None
    test_auroc: Optional[float] = None
    test_sensitivity: Optional[float] = None
    test_specificity: Optional[float] = None
    best_val_auroc: Optional[float] = None
    epochs_trained: Optional[int] = None


# ── Notifications ─────────────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    id: int
    type: str    # success | info | warning | error
    title: str
    msg: str
    time: str


# ── Generic ───────────────────────────────────────────────────────────────────

class StatusOut(BaseModel):
    ok: bool
    message: str


# ── Screening & Triage (Lab Technician) ───────────────────────────────────────

class FlagSignal(BaseModel):
    level: str             # warning | danger | info
    title: str
    message: str


class XAISegment(BaseModel):
    start_sec: float
    end_sec: float
    intensity: float       # 0.0 – 1.0 (Grad-CAM peak/mean intensity)
    label: str = "Suspected Murmur"


class ScreeningReportOut(BaseModel):
    report_id: str
    patient_id: str
    patient_name: str
    age_group: str         # Neonate | Infant | Child | Adolescent | Young Adult
    modality: str          # PCG | Echo
    prediction: str        # Normal | Abnormal
    confidence: float      # e.g. 0.92
    triage_recommendation: str
    flags: List[FlagSignal] = []
    xai_segments: List[XAISegment] = []
    ef_value: Optional[float] = None
    audio_url: Optional[str] = None
    ed_frame_url: Optional[str] = None
    es_frame_url: Optional[str] = None
    created_at: str
    status: str = "pending"   # pending | escalated | dismissed
    escalated_at: Optional[str] = None
    doctor_notes: Optional[str] = None
    technician_notes: Optional[str] = None


class ScreeningHistoryItem(BaseModel):
    report_id: str
    patient_id: str
    patient_name: str
    age_group: str
    modality: str
    prediction: str
    confidence: float
    flags_count: int
    created_at: str
    status: str


class DemoSampleOut(BaseModel):
    sample_id: str
    name: str
    patient_name: str
    age_group: str
    modality: str
    expected_type: str
    description: str
    duration_sec: Optional[float] = None
