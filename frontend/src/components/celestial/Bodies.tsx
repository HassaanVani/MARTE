/**
 * Shared realistic celestial body components.
 * Used by both Observer (OrbitalView) and Kinetic (CelestialObjects) views.
 *
 * - RealisticSun: procedural animated plasma surface + corona glow
 * - RealisticEarth: NASA Blue Marble texture + clouds + atmosphere + slow rotation
 */

import { useTexture } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import {
  sunCoronaFragmentShader,
  sunCoronaVertexShader,
  sunFragmentShader,
  sunVertexShader,
} from "./sunShader";

// ----- Sun -----

interface SunProps {
  radius?: number;
}

export function RealisticSun({ radius = 0.5 }: SunProps) {
  const surfaceRef = useRef<THREE.ShaderMaterial>(null);
  const coronaRef = useRef<THREE.ShaderMaterial>(null);

  const surfaceUniforms = useMemo(
    () => ({ uTime: { value: 0 } }),
    [],
  );
  const coronaUniforms = useMemo(
    () => ({ uTime: { value: 0 } }),
    [],
  );

  useFrame((_, delta) => {
    if (surfaceRef.current) surfaceRef.current.uniforms.uTime!.value += delta;
    if (coronaRef.current) coronaRef.current.uniforms.uTime!.value += delta;
  });

  return (
    <group>
      {/* Core surface */}
      <mesh>
        <sphereGeometry args={[radius, 64, 64]} />
        <shaderMaterial
          ref={surfaceRef}
          vertexShader={sunVertexShader}
          fragmentShader={sunFragmentShader}
          uniforms={surfaceUniforms}
        />
      </mesh>

      {/* Inner corona glow */}
      <mesh>
        <sphereGeometry args={[radius * 1.15, 48, 48]} />
        <shaderMaterial
          ref={coronaRef}
          vertexShader={sunCoronaVertexShader}
          fragmentShader={sunCoronaFragmentShader}
          uniforms={coronaUniforms}
          transparent
          side={THREE.BackSide}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>

      {/* Outer haze */}
      <mesh>
        <sphereGeometry args={[radius * 2.0, 32, 32]} />
        <meshBasicMaterial
          color="#ffa020"
          transparent
          opacity={0.06}
          side={THREE.BackSide}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>

      {/* Point light from the Sun */}
      <pointLight intensity={8} color="#ffeedd" distance={500} decay={1} />
    </group>
  );
}

// ----- Earth -----

interface EarthProps {
  radius?: number;
}

export function RealisticEarth({ radius = 0.2 }: EarthProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const cloudsRef = useRef<THREE.Mesh>(null);

  const [dayMap, bumpMap, cloudsMap, nightMap] = useTexture([
    "/textures/earth_daymap.jpg",
    "/textures/earth_bumpmap.jpg",
    "/textures/earth_clouds.png",
    "/textures/earth_nightmap.jpg",
  ]);

  // Slow rotation
  useFrame((_, delta) => {
    if (meshRef.current) meshRef.current.rotation.y += delta * 0.1;
    if (cloudsRef.current) cloudsRef.current.rotation.y += delta * 0.12;
  });

  return (
    <group>
      {/* Earth surface */}
      <mesh ref={meshRef}>
        <sphereGeometry args={[radius, 48, 48]} />
        <meshStandardMaterial
          map={dayMap}
          bumpMap={bumpMap}
          bumpScale={0.02}
          emissiveMap={nightMap}
          emissive={new THREE.Color(0.3, 0.3, 0.5)}
          emissiveIntensity={0.8}
          roughness={0.7}
          metalness={0.0}
        />
      </mesh>

      {/* Cloud layer */}
      <mesh ref={cloudsRef}>
        <sphereGeometry args={[radius * 1.01, 48, 48]} />
        <meshStandardMaterial
          alphaMap={cloudsMap}
          transparent
          opacity={0.35}
          color="#ffffff"
          depthWrite={false}
        />
      </mesh>

      {/* Atmosphere glow (fresnel effect via BackSide rendering) */}
      <mesh>
        <sphereGeometry args={[radius * 1.12, 48, 48]} />
        <meshBasicMaterial
          color="#4488ff"
          transparent
          opacity={0.1}
          side={THREE.BackSide}
          depthWrite={false}
        />
      </mesh>
    </group>
  );
}

// ----- Ghost Earth (light-delayed apparent position) -----

export function GhostEarth({ radius = 0.18 }: { radius?: number }) {
  return (
    <group>
      <mesh>
        <sphereGeometry args={[radius, 24, 24]} />
        <meshBasicMaterial
          color="#6699ff"
          wireframe
          transparent
          opacity={0.2}
        />
      </mesh>
    </group>
  );
}
