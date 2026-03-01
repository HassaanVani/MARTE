import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import type { InterpolatedState } from "../../types";

interface Props {
  interpolated: InterpolatedState | null;
}

const AU_SCALE = 10;

function EngineGlow({ interpolated }: Props) {
  const meshRef = useRef<THREE.Mesh>(null);
  const lightRef = useRef<THREE.PointLight>(null);

  useFrame(() => {
    if (!interpolated || !meshRef.current || !lightRef.current) return;

    // Engine fires opposite to velocity direction (behind the ship)
    const vDir = interpolated.velocityDirection;
    const isThrusting =
      interpolated.phase === "ACCELERATING" || interpolated.phase === "DECELERATING";
    const intensity = isThrusting ? 0.5 + interpolated.beta * 2.0 : 0;

    // Position behind ship (ship is at origin in kinetic frame)
    meshRef.current.position.set(-vDir[0] * 0.5, -vDir[1] * 0.5, -vDir[2] * 0.5);
    meshRef.current.scale.setScalar(intensity > 0 ? 0.15 + intensity * 0.2 : 0.001);

    lightRef.current.position.copy(meshRef.current.position);
    lightRef.current.intensity = intensity * 3;
  });

  return (
    <>
      <mesh ref={meshRef}>
        <sphereGeometry args={[1, 16, 16]} />
        <meshBasicMaterial
          color="#00ccff"
          transparent
          opacity={0.6}
        />
      </mesh>
      <pointLight ref={lightRef} color="#00ccff" distance={20} />
    </>
  );
}

function Sun({ interpolated }: Props) {
  const groupRef = useRef<THREE.Group>(null);
  const glowRef = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (!interpolated || !groupRef.current) return;
    const shipPos = interpolated.positionAU;
    groupRef.current.position.set(
      -shipPos[0] * AU_SCALE,
      -shipPos[1] * AU_SCALE,
      -shipPos[2] * AU_SCALE,
    );
    // Subtle pulse
    if (glowRef.current) {
      const pulse = 1.0 + Math.sin(clock.getElapsedTime() * 2) * 0.05;
      glowRef.current.scale.setScalar(pulse);
    }
  });

  const sunMat = useMemo(
    () =>
      new THREE.MeshBasicMaterial({
        color: new THREE.Color("#fbbf24"),
      }),
    [],
  );

  return (
    <group ref={groupRef}>
      <mesh material={sunMat}>
        <sphereGeometry args={[0.6, 32, 32]} />
      </mesh>
      {/* Glow halo */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[1.2, 32, 32]} />
        <meshBasicMaterial
          color="#fbbf24"
          transparent
          opacity={0.15}
          side={THREE.BackSide}
        />
      </mesh>
      <pointLight intensity={8} color="#fbbf24" distance={300} decay={1} />
    </group>
  );
}

function Earth({ interpolated }: Props) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame(() => {
    if (!interpolated || !groupRef.current) return;
    const shipPos = interpolated.positionAU;
    const earthPos = interpolated.earthPositionAU;
    groupRef.current.position.set(
      (earthPos[0] - shipPos[0]) * AU_SCALE,
      (earthPos[1] - shipPos[1]) * AU_SCALE,
      (earthPos[2] - shipPos[2]) * AU_SCALE,
    );
  });

  return (
    <group ref={groupRef}>
      <mesh>
        <sphereGeometry args={[0.2, 24, 24]} />
        <meshStandardMaterial
          color="#4488ff"
          emissive="#2244aa"
          emissiveIntensity={0.8}
        />
      </mesh>
      {/* Atmosphere glow */}
      <mesh>
        <sphereGeometry args={[0.28, 24, 24]} />
        <meshBasicMaterial
          color="#6699ff"
          transparent
          opacity={0.12}
          side={THREE.BackSide}
        />
      </mesh>
    </group>
  );
}

export function CelestialObjects({ interpolated }: Props) {
  return (
    <>
      <Sun interpolated={interpolated} />
      <Earth interpolated={interpolated} />
      <EngineGlow interpolated={interpolated} />
    </>
  );
}
