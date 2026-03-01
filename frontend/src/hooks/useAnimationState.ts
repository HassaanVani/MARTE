import { useCallback, useEffect, useRef, useState } from "react";

const BASE_DURATION_MS = 10_000; // Full trajectory in 10s at 1x

export interface AnimationControls {
  progress: number;
  playing: boolean;
  speed: number;
  play: () => void;
  pause: () => void;
  seek: (p: number) => void;
  setSpeed: (s: number) => void;
  reset: () => void;
}

export function useAnimationState(): AnimationControls {
  const [progress, setProgress] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeedState] = useState(1);

  const progressRef = useRef(0);
  const playingRef = useRef(false);
  const speedRef = useRef(1);
  const lastFrameRef = useRef(0);
  const rafRef = useRef(0);

  const tick = useCallback((now: number) => {
    if (!playingRef.current) return;

    if (lastFrameRef.current > 0) {
      const dt = now - lastFrameRef.current;
      const dp = (dt / BASE_DURATION_MS) * speedRef.current;
      const next = Math.min(1, progressRef.current + dp);
      progressRef.current = next;
      setProgress(next);

      if (next >= 1) {
        playingRef.current = false;
        setPlaying(false);
        lastFrameRef.current = 0;
        return;
      }
    }

    lastFrameRef.current = now;
    rafRef.current = requestAnimationFrame(tick);
  }, []);

  const play = useCallback(() => {
    if (progressRef.current >= 1) {
      progressRef.current = 0;
      setProgress(0);
    }
    playingRef.current = true;
    setPlaying(true);
    lastFrameRef.current = 0;
    rafRef.current = requestAnimationFrame(tick);
  }, [tick]);

  const pause = useCallback(() => {
    playingRef.current = false;
    setPlaying(false);
    lastFrameRef.current = 0;
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
  }, []);

  const seek = useCallback((p: number) => {
    const clamped = Math.max(0, Math.min(1, p));
    progressRef.current = clamped;
    setProgress(clamped);
    lastFrameRef.current = 0;
  }, []);

  const setSpeed = useCallback((s: number) => {
    speedRef.current = s;
    setSpeedState(s);
  }, []);

  const reset = useCallback(() => {
    pause();
    progressRef.current = 0;
    setProgress(0);
  }, [pause]);

  useEffect(() => {
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return { progress, playing, speed, play, pause, seek, setSpeed, reset };
}
