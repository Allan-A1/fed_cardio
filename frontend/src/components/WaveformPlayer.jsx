import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Play, Pause, Square, RotateCcw, Volume2, VolumeX, Sparkles, FastForward } from 'lucide-react';

export default function WaveformPlayer({ audioUrl, xaiSegments = [], height = 140 }) {
  const canvasRef = useRef(null);
  const audioRef = useRef(null);
  const audioCtxRef = useRef(null);
  const audioBufferRef = useRef(null);
  const animFrameRef = useRef(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const [isMuted, setIsMuted] = useState(false);
  const [loopSegment, setLoopSegment] = useState(null);
  const [error, setError] = useState(null);

  // Format time mm:ss.s
  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '00:00.0';
    const m = Math.floor(seconds / 60);
    const s = (seconds % 60).toFixed(1);
    return `${m.toString().padStart(2, '0')}:${s.padStart(4, '0')}`;
  };

  // Decode audio data for canvas waveform visualization
  useEffect(() => {
    if (!audioUrl) {
      setIsLoading(false);
      return;
    }

    let isMounted = true;
    setIsLoading(true);
    setError(null);

    const loadAudio = async () => {
      try {
        const response = await fetch(audioUrl);
        if (!response.ok) {
          throw new Error(`Failed to load audio (${response.status})`);
        }
        const arrayBuffer = await response.arrayBuffer();

        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (!audioCtxRef.current) {
          audioCtxRef.current = new AudioContextClass();
        }

        const decodedBuffer = await audioCtxRef.current.decodeAudioData(arrayBuffer.slice(0));
        if (isMounted) {
          audioBufferRef.current = decodedBuffer;
          setDuration(decodedBuffer.duration);
          setIsLoading(false);
        }
      } catch (err) {
        console.error('Audio decode error:', err);
        if (isMounted) {
          setError('Could not decode audio waveform.');
          setIsLoading(false);
        }
      }
    };

    loadAudio();

    return () => {
      isMounted = false;
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [audioUrl]);

  // Render canvas waveform with XAI segments and playhead
  const drawWaveform = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, width, h);

    const buffer = audioBufferRef.current;
    const dur = duration || (buffer ? buffer.duration : 1);

    // 1. Draw Background grid lines
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.04)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, h / 2);
    ctx.lineTo(width, h / 2);
    ctx.stroke();

    // 2. Draw Grad-CAM Saliency Highlight Zones
    if (xaiSegments && xaiSegments.length > 0 && dur > 0) {
      xaiSegments.forEach((seg, idx) => {
        const xStart = Math.max(0, (seg.start_sec / dur) * width);
        const xEnd = Math.min(width, (seg.end_sec / dur) * width);
        const segWidth = Math.max(4, xEnd - xStart);

        // Highlight zone background
        const grad = ctx.createLinearGradient(xStart, 0, xStart, h);
        grad.addColorStop(0, 'rgba(239, 68, 68, 0.28)');
        grad.addColorStop(0.5, 'rgba(239, 68, 68, 0.16)');
        grad.addColorStop(1, 'rgba(239, 68, 68, 0.28)');

        ctx.fillStyle = grad;
        ctx.fillRect(xStart, 0, segWidth, h);

        // Segment border lines
        ctx.strokeStyle = 'rgba(239, 68, 68, 0.85)';
        ctx.lineWidth = 1.5;
        ctx.strokeRect(xStart, 0, segWidth, h);

        // Segment header tag on canvas
        ctx.fillStyle = 'rgba(239, 68, 68, 0.9)';
        ctx.fillRect(xStart, 0, Math.min(segWidth, 120), 18);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 9px Inter, sans-serif';
        ctx.fillText(`FLAGGED: ${seg.start_sec.toFixed(1)}s-${seg.end_sec.toFixed(1)}s`, xStart + 4, 12);
      });
    }

    // 3. Draw Waveform Peaks
    if (buffer) {
      const rawData = buffer.getChannelData(0);
      const step = Math.ceil(rawData.length / width);
      const amp = h / 2.2;

      ctx.fillStyle = 'hsl(221, 100%, 55%)';
      for (let i = 0; i < width; i++) {
        let min = 1.0;
        let max = -1.0;
        for (let j = 0; j < step; j++) {
          const datum = rawData[i * step + j];
          if (datum < min) min = datum;
          if (datum > max) max = datum;
        }

        // Check if inside a flagged XAI zone to color wave in warning red/amber
        const timeAtPixel = (i / width) * dur;
        const inFlagged = xaiSegments.some(
          (s) => timeAtPixel >= s.start_sec && timeAtPixel <= s.end_sec
        );

        if (inFlagged) {
          ctx.fillStyle = 'hsl(0, 84%, 56%)';
        } else {
          ctx.fillStyle = 'hsl(221, 80%, 48%)';
        }

        const barHeight = Math.max(2, (max - min) * amp);
        const y = (h - barHeight) / 2;
        ctx.fillRect(i, y, 1.2, barHeight);
      }
    } else {
      // Synthetic fallback preview waveform while loading
      ctx.fillStyle = 'hsla(221, 50%, 60%, 0.4)';
      for (let i = 0; i < width; i += 3) {
        const val = Math.sin(i * 0.05) * Math.cos(i * 0.02) * (h * 0.35);
        ctx.fillRect(i, h / 2 - Math.abs(val) / 2, 2, Math.max(2, Math.abs(val)));
      }
    }

    // 4. Draw Current Playhead Cursor
    if (dur > 0) {
      const playheadX = (currentTime / dur) * width;

      // Glow line
      ctx.shadowColor = 'hsl(221, 100%, 55%)';
      ctx.shadowBlur = 8;
      ctx.strokeStyle = '#2563eb';
      ctx.lineWidth = 2.5;

      ctx.beginPath();
      ctx.moveTo(playheadX, 0);
      ctx.lineTo(playheadX, h);
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Playhead top marker triangle
      ctx.fillStyle = '#2563eb';
      ctx.beginPath();
      ctx.moveTo(playheadX - 5, 0);
      ctx.lineTo(playheadX + 5, 0);
      ctx.lineTo(playheadX, 8);
      ctx.closePath();
      ctx.fill();
    }
  }, [duration, currentTime, xaiSegments]);

  // Redraw when state updates
  useEffect(() => {
    drawWaveform();
  }, [drawWaveform]);

  // Audio element timeupdate & loop listener
  const handleTimeUpdate = () => {
    if (!audioRef.current) return;
    const time = audioRef.current.currentTime;
    setCurrentTime(time);

    // If loop segment is active, loop within start and end
    if (loopSegment && time >= loopSegment.end_sec) {
      audioRef.current.currentTime = loopSegment.start_sec;
    }
  };

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleStop = () => {
    if (!audioRef.current) return;
    audioRef.current.pause();
    audioRef.current.currentTime = 0;
    setCurrentTime(0);
    setIsPlaying(false);
    setLoopSegment(null);
  };

  // Canvas click or scrub to seek
  const handleCanvasClick = (e) => {
    const canvas = canvasRef.current;
    if (!canvas || !audioRef.current) return;
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const pct = Math.max(0, Math.min(1, clickX / rect.width));
    const seekTime = pct * duration;
    audioRef.current.currentTime = seekTime;
    setCurrentTime(seekTime);
  };

  // Jump to specific XAI segment
  const jumpToSegment = (seg, loop = false) => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = Math.max(0, seg.start_sec - 0.2);
    setCurrentTime(audioRef.current.currentTime);
    if (loop) {
      setLoopSegment(seg);
    } else {
      setLoopSegment(null);
    }
    audioRef.current.play();
    setIsPlaying(true);
  };

  const changeSpeed = (speed) => {
    setPlaybackRate(speed);
    if (audioRef.current) {
      audioRef.current.playbackRate = speed;
    }
  };

  return (
    <div
      className="card"
      style={{
        padding: 'var(--sp-6)',
        background: 'var(--bg-surface)',
        borderColor: 'var(--border-default)',
      }}
    >
      {/* Hidden HTML5 Audio Element */}
      <audio
        ref={audioRef}
        src={audioUrl}
        onTimeUpdate={handleTimeUpdate}
        onEnded={() => {
          setIsPlaying(false);
          setLoopSegment(null);
        }}
        preload="auto"
      />

      {/* Header Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
        <div>
          <h4 style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>
            Heart Sound Auscultation Waveform (PCG)
          </h4>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Deep Learning Grad-CAM Murmur Activation Overlaid (4000 Hz Sampling)
          </span>
        </div>

        {/* Time Stamp display */}
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '15px',
            fontWeight: '600',
            color: 'var(--text-primary)',
            background: 'var(--bg-elevated)',
            padding: '4px 12px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <span style={{ color: 'var(--brand-primary)' }}>{formatTime(currentTime)}</span>
          <span style={{ color: 'var(--text-muted)' }}> / {formatTime(duration)}</span>
        </div>
      </div>

      {/* Canvas Waveform Container */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          background: 'hsl(210, 25%, 97%)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-default)',
          overflow: 'hidden',
          cursor: 'pointer',
        }}
      >
        <canvas
          ref={canvasRef}
          width={800}
          height={height}
          onClick={handleCanvasClick}
          style={{ width: '100%', height: `${height}px`, display: 'block' }}
        />

        {isLoading && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(255, 255, 255, 0.75)',
              fontSize: '13px',
              fontWeight: '600',
              color: 'var(--text-secondary)',
            }}
          >
            Decoding PCG audio stream...
          </div>
        )}

        {error && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(255, 255, 255, 0.85)',
              fontSize: '13px',
              color: 'var(--brand-danger)',
            }}
          >
            {error}
          </div>
        )}
      </div>

      {/* Flagged Segments Banner */}
      {xaiSegments && xaiSegments.length > 0 && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            flexWrap: 'wrap',
            marginTop: '12px',
            padding: '10px 14px',
            background: 'hsla(0, 84%, 60%, 0.08)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid hsla(0, 84%, 60%, 0.25)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginRight: '4px' }}>
            <Sparkles size={16} color="var(--brand-danger)" />
            <span style={{ fontSize: '13px', fontWeight: '700', color: 'hsl(0, 75%, 45%)' }}>
              AI Saliency Hotspots:
            </span>
          </div>

          {xaiSegments.map((seg, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <button
                className="btn btn-sm"
                style={{
                  background: '#fff',
                  borderColor: 'hsla(0, 84%, 60%, 0.4)',
                  color: 'hsl(0, 75%, 45%)',
                  fontWeight: '600',
                  fontSize: '12px',
                  padding: '3px 10px',
                }}
                onClick={() => jumpToSegment(seg, false)}
                title="Jump to this segment"
              >
                ▶ {seg.start_sec.toFixed(1)}s – {seg.end_sec.toFixed(1)}s ({Math.round(seg.intensity * 100)}% salience)
              </button>
              <button
                className="btn btn-sm btn-ghost"
                style={{
                  color: loopSegment === seg ? 'var(--brand-primary)' : 'var(--text-secondary)',
                  fontWeight: '600',
                  fontSize: '11px',
                  padding: '3px 6px',
                }}
                onClick={() => jumpToSegment(seg, true)}
                title="Loop this segment"
              >
                🔁 Loop
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Audio Controls Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
          marginTop: '14px',
          paddingTop: '12px',
          borderTop: '1px solid var(--border-subtle)',
        }}
      >
        {/* Left: Playback controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            className="btn btn-primary"
            onClick={togglePlay}
            id="btn-play-pause"
            style={{ width: '40px', height: '40px', padding: 0, borderRadius: '50%' }}
          >
            {isPlaying ? <Pause size={18} /> : <Play size={18} style={{ marginLeft: '2px' }} />}
          </button>

          <button
            className="btn btn-ghost btn-icon"
            onClick={handleStop}
            title="Stop & Reset"
            style={{ color: 'var(--text-secondary)' }}
          >
            <Square size={16} />
          </button>

          <button
            className="btn btn-ghost btn-icon"
            onClick={() => {
              if (audioRef.current) {
                audioRef.current.currentTime = 0;
                setCurrentTime(0);
              }
            }}
            title="Restart"
            style={{ color: 'var(--text-secondary)' }}
          >
            <RotateCcw size={16} />
          </button>
        </div>

        {/* Center: Auscultation Slow-Motion Speeds */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)' }}>
            Speed:
          </span>
          {[0.5, 0.75, 1.0].map((rate) => (
            <button
              key={rate}
              className={`btn btn-sm ${playbackRate === rate ? 'btn-primary' : 'btn-ghost'}`}
              style={{
                padding: '3px 8px',
                fontSize: '11px',
                fontWeight: '700',
              }}
              onClick={() => changeSpeed(rate)}
            >
              {rate}x {rate < 1.0 ? '(Auscultate)' : ''}
            </button>
          ))}
        </div>

        {/* Right: Audio Mute */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            className="btn btn-ghost btn-icon"
            onClick={() => {
              if (audioRef.current) {
                audioRef.current.muted = !isMuted;
                setIsMuted(!isMuted);
              }
            }}
            title={isMuted ? 'Unmute' : 'Mute'}
            style={{ color: isMuted ? 'var(--brand-danger)' : 'var(--text-secondary)' }}
          >
            {isMuted ? <VolumeX size={18} /> : <Volume2 size={18} />}
          </button>
        </div>
      </div>
    </div>
  );
}
