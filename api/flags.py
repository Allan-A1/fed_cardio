"""
Signal Flagging & Clinical Quality Rules Engine
================================================
Evaluates signal quality, patient demographics, and model confidence thresholds
to output explicit warnings and decision flags for lab technicians.
"""
from typing import List, Optional
import numpy as np
from api.schemas import FlagSignal


def evaluate_pcg_flags(
    audio: Optional[np.ndarray],
    sample_rate: int,
    age_group: str,
    prediction: str,
    confidence: float,
) -> List[FlagSignal]:
    """Generate risk and signal quality flags for a PCG screening."""
    flags: List[FlagSignal] = []

    # 1. Age group considerations
    norm_age = (age_group or "").strip().title()
    if norm_age == "Neonate":
        flags.append(FlagSignal(
            level="warning",
            title="High-Sensitivity Age: Neonate",
            message="Neonates exhibit rapid hemodynamic changes and benign physiological murmurs are prevalent. Doctor confirmation is highly recommended."
        ))
    elif norm_age == "Infant":
        flags.append(FlagSignal(
            level="info",
            title="Pediatric Patient: Infant",
            message="Pediatric acoustic baseline applied (0–12 months). Elevated heart rates can compress diastole."
        ))

    # 2. Model Confidence Triage
    if 0.48 <= confidence <= 0.68:
        flags.append(FlagSignal(
            level="warning",
            title="Borderline Decision Boundary",
            message=f"Model output is near decision threshold with {confidence*100:.1f}% confidence. Automated classification is equivocal; direct physician review required."
        ))
    elif confidence < 0.48:
        flags.append(FlagSignal(
            level="danger",
            title="Uncertain Automated Classification",
            message=f"Model confidence is low ({confidence*100:.1f}%). Auscultation recording should be retaken or evaluated manually by a pediatric cardiologist."
        ))

    # 3. Audio Signal Quality Checks (if raw audio is provided)
    if audio is not None and len(audio) > 0:
        duration_sec = len(audio) / float(sample_rate)

        # Duration check
        if duration_sec < 3.0:
            flags.append(FlagSignal(
                level="warning",
                title="Short Recording Duration",
                message=f"Recording is only {duration_sec:.1f}s long. Recommended recording duration is ≥ 5s to capture complete S1-S2 heart sound cycles."
            ))

        # Clipping / Saturation check
        peak_amp = float(np.max(np.abs(audio)))
        if peak_amp >= 0.98:
            flags.append(FlagSignal(
                level="danger",
                title="Microphone Clipping Detected",
                message="Audio amplitude hits sensor saturation limits (≥ 0.98). Clipping induces artificial harmonics that may mimic murmur frequencies."
            ))
        elif peak_amp < 0.03:
            flags.append(FlagSignal(
                level="warning",
                title="Low Signal Amplitude",
                message="Very faint acoustic signal detected. Ensure stethoscope diaphragm has firm skin contact."
            ))

        # Simple Noise/SNR check via RMS vs peak
        rms = float(np.sqrt(np.mean(audio ** 2)))
        crest_factor = (peak_amp / (rms + 1e-6))
        if rms > 0.35 and crest_factor < 2.0:
            flags.append(FlagSignal(
                level="warning",
                title="High Background Acoustic Noise",
                message="High continuous ambient energy detected. Check for respiratory interference, crying, or ambient room noise."
            ))

    # 4. Result-specific flags
    if prediction == "Abnormal":
        flags.append(FlagSignal(
            level="danger",
            title="Structural Acoustic Anomaly Flagged",
            message="Acoustic patterns correspond to systolic/diastolic murmur components (sensitivity threshold triggered)."
        ))

    return flags


def evaluate_echo_flags(
    ef_value: Optional[float],
    age_group: str,
    prediction: str,
    confidence: float,
) -> List[FlagSignal]:
    """Generate risk and signal quality flags for an Echo screening."""
    flags: List[FlagSignal] = []

    norm_age = (age_group or "").strip().title()
    if norm_age in ["Neonate", "Infant"]:
        flags.append(FlagSignal(
            level="info",
            title=f"Pediatric Subject: {norm_age}",
            message="ASE pediatric left ventricular quantification guidelines apply."
        ))

    if ef_value is not None:
        if ef_value < 50.0:
            flags.append(FlagSignal(
                level="danger",
                title="Severely Reduced Ejection Fraction",
                message=f"Calculated Ejection Fraction is {ef_value:.1f}%, significantly below normal (>55%). Immediate clinical escalation required."
            ))
        elif ef_value < 55.0:
            flags.append(FlagSignal(
                level="danger",
                title="Reduced Left Ventricle Systolic Function",
                message=f"Ejection Fraction is {ef_value:.1f}% (pediatric abnormal threshold < 55%)."
            ))
        elif ef_value <= 58.0:
            flags.append(FlagSignal(
                level="warning",
                title="Borderline Ejection Fraction",
                message=f"Ejection Fraction is {ef_value:.1f}%, hovering in the lower normal range (55–58%)."
            ))
        else:
            flags.append(FlagSignal(
                level="info",
                title="Normal Systolic Contractility",
                message=f"Ejection Fraction is {ef_value:.1f}%, within healthy pediatric parameters."
            ))

    if 0.48 <= confidence <= 0.65:
        flags.append(FlagSignal(
            level="warning",
            title="Borderline Model Certainty",
            message=f"Model confidence is {confidence*100:.1f}%. Frame contrast or acoustic shadow may affect tracking."
        ))

    return flags
