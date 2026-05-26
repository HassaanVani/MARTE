import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import type { InterpolatedState } from "../../types";
import {
  starfieldFragmentShader,
  starfieldVertexShader,
} from "./starfieldShader";

interface Props {
  interpolated: InterpolatedState | null;
}

const STAR_COUNT = 20_000;
const BOX_SIZE = 20000;
const AU_SCALE = 10;

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

  const starData = useMemo(() => {
    const pos = new Float32Array(STAR_COUNT * 3);
    const sz = new Float32Array(STAR_COUNT);
    const col = new Float32Array(STAR_COUNT * 3);
    const bright = new Float32Array(STAR_COUNT);
    const temp = new Float32Array(STAR_COUNT);

    for (let i = 0; i < STAR_COUNT; i++) {
      // Randomize stars within the 3D box volume
      pos[i * 3] = (Math.random() - 0.5) * BOX_SIZE;
      pos[i * 3 + 1] = (Math.random() - 0.5) * BOX_SIZE;
      pos[i * 3 + 2] = (Math.random() - 0.5) * BOX_SIZE;

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

  const starUniforms = useMemo(
    () => ({
      uBeta: { value: 0.0 },
      uGamma: { value: 1.0 },
      uVelocityDir: { value: new THREE.Vector3(1, 0, 0) },
      uShipPosition: { value: new THREE.Vector3(0, 0, 0) },
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
      const shipPos = interpolated?.positionAU ?? [0, 0, 0];
      u.uShipPosition!.value.set(shipPos[0] * AU_SCALE, shipPos[1] * AU_SCALE, shipPos[2] * AU_SCALE);
    }
  });

  const starGeometry = useMemo(() => {
    const geom = new THREE.PlaneGeometry(1, 1);
    geom.setAttribute("aOffset", new THREE.InstancedBufferAttribute(starData.positions, 3));
    geom.setAttribute("aSize", new THREE.InstancedBufferAttribute(starData.sizes, 1));
    geom.setAttribute("aColor", new THREE.InstancedBufferAttribute(starData.colors, 3));
    geom.setAttribute("aBrightness", new THREE.InstancedBufferAttribute(starData.brightness, 1));
    geom.setAttribute("aTemperature", new THREE.InstancedBufferAttribute(starData.temperatures, 1));
    return geom;
  }, [starData]);

  return (
    <>
      {/* Stars */}
      <instancedMesh args={[starGeometry, undefined, STAR_COUNT]} frustumCulled={false}>
        <shaderMaterial
          ref={starMatRef}
          vertexShader={starfieldVertexShader}
          fragmentShader={starfieldFragmentShader}
          uniforms={starUniforms}
          transparent
          depthWrite={false}
          blending={THREE.AdditiveBlending}
          side={THREE.DoubleSide}
        />
      </instancedMesh>
    </>
  );
}
