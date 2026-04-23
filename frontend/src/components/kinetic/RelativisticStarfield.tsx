import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import type { InterpolatedState } from "../../types";
import {
  starfieldFragmentShader,
  starfieldVertexShader,
  warpFragmentShader,
  warpVertexShader,
} from "./starfieldShader";

interface Props {
  interpolated: InterpolatedState | null;
}

const STAR_COUNT = 20_000;
const SPHERE_RADIUS = 500;
const WARP_LINE_COUNT = 600;

/**
 * Generate a star temperature (Kelvin) from a rough Hertzsprung–Russell distribution.
 * Most stars are cool red dwarfs; a few are hot blue giants.
 */
function randomStarTemperature(): number {
  const r = Math.random();
  // Approximate main-sequence temperature distribution
  if (r < 0.02) return 25000 + Math.random() * 15000;    // O/B: hot blue (2%)
  if (r < 0.06) return 10000 + Math.random() * 5000;     // A: white-blue (4%)
  if (r < 0.12) return 7500 + Math.random() * 2500;      // F: yellow-white (6%)
  if (r < 0.25) return 5500 + Math.random() * 2000;      // G: Sol-like (13%)
  if (r < 0.45) return 4000 + Math.random() * 1500;      // K: orange (20%)
  return 2500 + Math.random() * 1500;                     // M: red dwarf (55%)
}

/**
 * Map a star temperature to an approximate RGB color for the non-Doppler baseline.
 */
function tempToBaseColor(temp: number): [number, number, number] {
  // Simplified blackbody → sRGB mapping
  if (temp > 20000) return [0.6, 0.7, 1.0];      // hot blue
  if (temp > 10000) return [0.75, 0.82, 1.0];     // blue-white
  if (temp > 7500)  return [0.95, 0.95, 1.0];     // white
  if (temp > 5500)  return [1.0, 0.96, 0.85];     // yellow
  if (temp > 4000)  return [1.0, 0.82, 0.55];     // orange
  return [1.0, 0.6, 0.35];                         // red
}

export function RelativisticStarfield({ interpolated }: Props) {
  const starMatRef = useRef<THREE.ShaderMaterial>(null);
  const warpMatRef = useRef<THREE.ShaderMaterial>(null);

  const starData = useMemo(() => {
    const pos = new Float32Array(STAR_COUNT * 3);
    const sz = new Float32Array(STAR_COUNT);
    const col = new Float32Array(STAR_COUNT * 3);
    const bright = new Float32Array(STAR_COUNT);
    const temp = new Float32Array(STAR_COUNT);

    for (let i = 0; i < STAR_COUNT; i++) {
      const theta = Math.acos(2 * Math.random() - 1);
      const phi = Math.random() * Math.PI * 2;

      pos[i * 3] = SPHERE_RADIUS * Math.sin(theta) * Math.cos(phi);
      pos[i * 3 + 1] = SPHERE_RADIUS * Math.sin(theta) * Math.sin(phi);
      pos[i * 3 + 2] = SPHERE_RADIUS * Math.cos(theta);

      // Star temperature drives both color and the spectral Doppler model
      const starTemp = randomStarTemperature();
      temp[i] = starTemp;

      // Vary sizes — hotter/brighter stars are bigger
      const r = Math.random();
      if (starTemp > 15000 && r < 0.5) {
        sz[i] = 4.0 + Math.random() * 3.0;
        bright[i] = 1.0;
      } else if (starTemp > 7000 && r < 0.3) {
        sz[i] = 2.5 + Math.random() * 2.0;
        bright[i] = 0.8 + Math.random() * 0.2;
      } else {
        sz[i] = 1.2 + Math.random() * 1.5;
        bright[i] = 0.4 + Math.random() * 0.4;
      }

      // Base color from temperature (used at low β before spectral model kicks in)
      const [cr, cg, cb] = tempToBaseColor(starTemp);
      col[i * 3] = cr;
      col[i * 3 + 1] = cg;
      col[i * 3 + 2] = cb;
    }

    return { positions: pos, sizes: sz, colors: col, brightness: bright, temperatures: temp };
  }, []);

  const warpData = useMemo(() => {
    const offsets = new Float32Array(WARP_LINE_COUNT);
    const speeds = new Float32Array(WARP_LINE_COUNT);
    const positions = new Float32Array(WARP_LINE_COUNT * 3);

    for (let i = 0; i < WARP_LINE_COUNT; i++) {
      offsets[i] = Math.random();
      speeds[i] = 0.3 + Math.random() * 0.7;
      positions[i * 3] = 0;
      positions[i * 3 + 1] = 0;
      positions[i * 3 + 2] = 0;
    }

    return { offsets, speeds, positions };
  }, []);

  const starUniforms = useMemo(
    () => ({
      uBeta: { value: 0.0 },
      uGamma: { value: 1.0 },
      uVelocityDir: { value: new THREE.Vector3(1, 0, 0) },
      uTime: { value: 0.0 },
    }),
    [],
  );

  const warpUniforms = useMemo(
    () => ({
      uBeta: { value: 0.0 },
      uVelocityDir: { value: new THREE.Vector3(1, 0, 0) },
      uTime: { value: 0.0 },
    }),
    [],
  );

  useFrame((_state, delta) => {
    const beta = interpolated?.beta ?? 0;
    const gamma = interpolated?.gamma ?? 1;
    const vDir = interpolated?.velocityDirection ?? [1, 0, 0];

    if (starMatRef.current) {
      const u = starMatRef.current.uniforms;
      u.uTime!.value += delta;
      u.uBeta!.value = beta;
      u.uGamma!.value = gamma;
      u.uVelocityDir!.value.set(vDir[0], vDir[1], vDir[2]);
    }

    if (warpMatRef.current) {
      const u = warpMatRef.current.uniforms;
      u.uTime!.value += delta;
      u.uBeta!.value = beta;
      u.uVelocityDir!.value.set(vDir[0], vDir[1], vDir[2]);
    }
  });

  return (
    <>
      {/* Stars */}
      <points>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[starData.positions, 3]} />
          <bufferAttribute attach="attributes-aSize" args={[starData.sizes, 1]} />
          <bufferAttribute attach="attributes-aColor" args={[starData.colors, 3]} />
          <bufferAttribute attach="attributes-aBrightness" args={[starData.brightness, 1]} />
          <bufferAttribute attach="attributes-aTemperature" args={[starData.temperatures, 1]} />
        </bufferGeometry>
        <shaderMaterial
          ref={starMatRef}
          vertexShader={starfieldVertexShader}
          fragmentShader={starfieldFragmentShader}
          uniforms={starUniforms}
          transparent
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </points>

      {/* Warp speed lines */}
      <points>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[warpData.positions, 3]} />
          <bufferAttribute attach="attributes-aOffset" args={[warpData.offsets, 1]} />
          <bufferAttribute attach="attributes-aSpeed" args={[warpData.speeds, 1]} />
        </bufferGeometry>
        <shaderMaterial
          ref={warpMatRef}
          vertexShader={warpVertexShader}
          fragmentShader={warpFragmentShader}
          uniforms={warpUniforms}
          transparent
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </points>
    </>
  );
}
