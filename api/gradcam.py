"""
Grad-CAM Explainable AI Engine for PCG Heart Sound Analysis
===========================================================
Extracts spatio-temporal gradient saliency from PCGNet to localize
the exact time intervals (in seconds) that triggered the 'Abnormal / Murmur'
decision.
"""
import os
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import torch
import torch.nn.functional as F

from api.schemas import XAISegment
from src.models.pcg_model import PCGNet, get_pcg_model
from src.preprocessing.pcg_pipeline import (
    SAMPLE_RATE,
    HOP_LENGTH,
    N_FFT,
    N_MELS,
    SEGMENT_SEC,
    compute_melspectrogram,
)

ROOT = Path(__file__).resolve().parent.parent
CKPT_PATH = ROOT / "outputs" / "checkpoints" / "pcg_best.pt"

_CACHED_MODEL: Optional[PCGNet] = None


def get_loaded_pcg_model() -> Optional[PCGNet]:
    """Load PCGNet weights once and cache in memory."""
    global _CACHED_MODEL
    if _CACHED_MODEL is not None:
        return _CACHED_MODEL

    if not CKPT_PATH.exists():
        return None

    try:
        model = get_pcg_model(embed_dim=128, dropout=0.0)
        state_dict = torch.load(CKPT_PATH, map_location="cpu", weights_only=True)
        model.load_state_dict(state_dict)
        model.eval()
        _CACHED_MODEL = model
        return _CACHED_MODEL
    except Exception as e:
        print(f"[GradCAM] Error loading model from {CKPT_PATH}: {e}")
        return None


def run_pcg_gradcam(
    spec_tensor: torch.Tensor,
    audio_duration_sec: float,
    target_class: int = 1,
    activation_threshold: float = 0.40,
) -> Tuple[List[XAISegment], np.ndarray]:
    """
    Run Grad-CAM on PCGNet given a spectrogram tensor of shape (1, 1, 64, T) or (1, 64, T).
    
    Returns:
        segments: List of XAISegment with start_sec, end_sec, intensity
        norm_curve: 1D normalized temporal activation curve [0, 1]
    """
    model = get_loaded_pcg_model()
    if model is None:
        # Fallback: estimate from energy in spectrogram
        return _heuristic_segments_from_spec(spec_tensor, audio_duration_sec)

    if spec_tensor.dim() == 2:
        spec_tensor = spec_tensor.unsqueeze(0).unsqueeze(0)
    elif spec_tensor.dim() == 3:
        spec_tensor = spec_tensor.unsqueeze(1)

    spec_tensor = spec_tensor.clone().detach().requires_grad_(True)

    # Hooks to capture gradients & activations at block3 conv
    activations = []
    gradients = []

    def fwd_hook(module, input, output):
        activations.append(output)

    def bwd_hook(module, grad_in, grad_out):
        gradients.append(grad_out[0])

    hook_fwd = model.block3.conv.register_forward_hook(fwd_hook)
    hook_bwd = model.block3.conv.register_full_backward_hook(bwd_hook)

    try:
        model.zero_grad()
        logits = model(spec_tensor)
        score = logits[0, target_class]
        score.backward()

        if not activations or not gradients:
            return _heuristic_segments_from_spec(spec_tensor, audio_duration_sec)

        act = activations[0].detach()     # (1, C, H, W)
        grad = gradients[0].detach()      # (1, C, H, W)

        # Global average pooling on gradients -> channel weights
        weights = torch.mean(grad, dim=(2, 3), keepdim=True)  # (1, C, 1, 1)
        cam = torch.sum(weights * act, dim=1, keepdim=True)     # (1, 1, H, W)
        cam = F.relu(cam)                                       # ReLU

        # Upsample CAM back to (64, T)
        cam_upsampled = F.interpolate(
            cam, size=spec_tensor.shape[-2:], mode="bilinear", align_corners=False
        )
        cam_2d = cam_upsampled.squeeze().cpu().numpy()  # (64, T)

        # Collapse across mel frequency bins to obtain 1D time activation profile
        time_curve = np.max(cam_2d, axis=0)
        t_min, t_max = time_curve.min(), time_curve.max()
        if t_max > t_min:
            norm_curve = (time_curve - t_min) / (t_max - t_min)
        else:
            norm_curve = np.zeros_like(time_curve)

        # Extract segments
        segments = _extract_segments_from_curve(
            norm_curve,
            duration_sec=audio_duration_sec,
            threshold=activation_threshold,
            min_duration=0.15,
        )
        return segments, norm_curve

    except Exception as e:
        print(f"[GradCAM] Error in forward/backward pass: {e}")
        return _heuristic_segments_from_spec(spec_tensor, audio_duration_sec)
    finally:
        hook_fwd.remove()
        hook_bwd.remove()


def _extract_segments_from_curve(
    curve: np.ndarray,
    duration_sec: float,
    threshold: float = 0.40,
    min_duration: float = 0.15,
) -> List[XAISegment]:
    """Turn 1D activation curve into discrete highlighted segments."""
    T = len(curve)
    if T == 0 or duration_sec <= 0:
        return []

    sec_per_frame = duration_sec / float(T)
    is_active = curve >= threshold

    segments: List[XAISegment] = []
    start_idx = None

    for i, active in enumerate(is_active):
        if active and start_idx is None:
            start_idx = i
        elif not active and start_idx is not None:
            end_idx = i
            seg_dur = (end_idx - start_idx) * sec_per_frame
            if seg_dur >= min_duration:
                intensity = float(np.mean(curve[start_idx:end_idx]))
                segments.append(XAISegment(
                    start_sec=round(start_idx * sec_per_frame, 2),
                    end_sec=round(end_idx * sec_per_frame, 2),
                    intensity=round(intensity, 2),
                    label="Acoustic Murmur Saliency"
                ))
            start_idx = None

    # Handle tail
    if start_idx is not None:
        end_idx = T
        seg_dur = (end_idx - start_idx) * sec_per_frame
        if seg_dur >= min_duration:
            intensity = float(np.mean(curve[start_idx:end_idx]))
            segments.append(XAISegment(
                start_sec=round(start_idx * sec_per_frame, 2),
                end_sec=round(end_idx * sec_per_frame, 2),
                intensity=round(intensity, 2),
                label="Acoustic Murmur Saliency"
            ))

    # Merge segments that are closer than 0.2s
    if len(segments) > 1:
        merged: List[XAISegment] = [segments[0]]
        for next_seg in segments[1:]:
            prev = merged[-1]
            if next_seg.start_sec - prev.end_sec < 0.20:
                merged[-1] = XAISegment(
                    start_sec=prev.start_sec,
                    end_sec=next_seg.end_sec,
                    intensity=round(max(prev.intensity, next_seg.intensity), 2),
                    label="Sustained Murmur Event"
                )
            else:
                merged.append(next_seg)
        segments = merged

    return segments


def _heuristic_segments_from_spec(
    spec_tensor: torch.Tensor,
    audio_duration_sec: float,
) -> Tuple[List[XAISegment], np.ndarray]:
    """Fallback if model checkpoint is unavailable: use spectral high-energy windows."""
    if isinstance(spec_tensor, torch.Tensor):
        spec = spec_tensor.squeeze().cpu().numpy()
    else:
        spec = np.array(spec_tensor)

    if spec.ndim == 2:
        high_freq_energy = np.mean(spec[16:48, :], axis=0)
    else:
        high_freq_energy = np.ones(100)

    e_min, e_max = high_freq_energy.min(), high_freq_energy.max()
    if e_max > e_min:
        norm = (high_freq_energy - e_min) / (e_max - e_min)
    else:
        norm = np.zeros_like(high_freq_energy)

    segs = _extract_segments_from_curve(norm, audio_duration_sec, threshold=0.65)
    return segs, norm
