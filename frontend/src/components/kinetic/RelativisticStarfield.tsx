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

const STAR_COUNT = 12000;
const SPHERE_RADIUS = 500;
const WARP_LINE_COUNT = 600;

export function RelativisticStarfield({ interpolated }: Props) {
  const starMatRef = useRef<THREE.ShaderMaterial>(null);
  const warpMatRef = useRef<THREE.ShaderMaterial>(null);

  const starData = useMemo(() => {
    const pos = new Float32Array(STAR_COUNT * 3);
    const sz = new Float32Array(STAR_COUNT);
    const col = new Float32Array(STAR_COUNT * 3);
    const bright = new Float32Array(STAR_COUNT);

    for (let i = 0; i < STAR_COUNT; i++) {
      const theta = Math.acos(2 * Math.random() - 1);
      const phi = Math.random() * Math.PI * 2;

      pos[i * 3] = SPHERE_RADIUS * Math.sin(theta) * Math.cos(phi);
      pos[i * 3 + 1] = SPHERE_RADIUS * Math.sin(theta) * Math.sin(phi);
      pos[i * 3 + 2] = SPHERE_RADIUS * Math.cos(theta);

      // Vary sizes more — some very bright stars
      const r = Math.random();
      if (r < 0.02) {
        sz[i] = 4.0 + Math.random() * 3.0; // Bright giants
        bright[i] = 1.0;
      } else if (r < 0.1) {
        sz[i] = 2.5 + Math.random() * 2.0;
        bright[i] = 0.8 + Math.random() * 0.2;
      } else {
        sz[i] = 1.2 + Math.random() * 1.5;
        bright[i] = 0.4 + Math.random() * 0.4;
      }

      // Star colors
      const roll = Math.random();
      if (roll < 0.04) {
        // Red giant — warm orange-red
        col[i * 3] = 1.0;
        col[i * 3 + 1] = 0.5 + Math.random() * 0.2;
        col[i * 3 + 2] = 0.2;
      } else if (roll < 0.08) {
        // Blue giant — hot blue-white
        col[i * 3] = 0.6;
        col[i * 3 + 1] = 0.7;
        col[i * 3 + 2] = 1.0;
      } else if (roll < 0.2) {
        // Yellow — Sol-like
        col[i * 3] = 1.0;
        col[i * 3 + 1] = 0.92;
        col[i * 3 + 2] = 0.7;
      } else if (roll < 0.35) {
        // Orange
        col[i * 3] = 1.0;
        col[i * 3 + 1] = 0.75;
        col[i * 3 + 2] = 0.5;
      } else {
        // White with slight variation
        const temp = 0.85 + Math.random() * 0.15;
        col[i * 3] = temp;
        col[i * 3 + 1] = temp;
        col[i * 3 + 2] = temp + Math.random() * 0.08;
      }
    }

    return { positions: pos, sizes: sz, colors: col, brightness: bright };
  }, []);

  const warpData = useMemo(() => {
    const offsets = new Float32Array(WARP_LINE_COUNT);
    const speeds = new Float32Array(WARP_LINE_COUNT);
    const positions = new Float32Array(WARP_LINE_COUNT * 3);

    for (let i = 0; i < WARP_LINE_COUNT; i++) {
      offsets[i] = Math.random();
      speeds[i] = 0.3 + Math.random() * 0.7;
      // Initial positions don't matter much — shader positions them
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
