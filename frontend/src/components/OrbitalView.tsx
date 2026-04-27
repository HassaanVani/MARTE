import { Html, Line, OrbitControls } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { Suspense, useMemo, useRef } from "react";
import * as THREE from "three";
import type { EarthData, InterpolatedState, TargetTrajectoryData, WorldlineData } from "../types";
import { RealisticEarth, RealisticSun } from "./celestial/Bodies";

interface Props {
  worldline: WorldlineData;
  earth: EarthData;
  interpolated: InterpolatedState | null;
  targetTrajectory?: TargetTrajectoryData | null;
}

const TARGET_COLORS: Record<string, string> = {
  Mercury: "#a0a0a0",
  Venus: "#e8c547",
  Mars: "#ef4444",
  Jupiter: "#f97316",
};

function OrbitRing({ radius, color, dashed = true }: { radius: number; color: string; dashed?: boolean }) {
  const points = useMemo(() => {
    const pts: [number, number, number][] = [];
    for (let i = 0; i <= 360; i++) {
      const a = (i * Math.PI) / 180;
      pts.push([radius * Math.cos(a), radius * Math.sin(a), 0]);
    }
    return pts;
  }, [radius]);
  if (dashed) {
    return <Line points={points} color={color} lineWidth={1} dashed dashScale={40} dashSize={1} gapSize={1} />;
  }
  return <Line points={points} color={color} lineWidth={1} />;
}

function TrajectoryLine({ positions, color }: { positions: number[][]; color: string }) {
  const pts = useMemo(
    () => positions.map((p) => [p[0]!, p[1]!, p[2]!] as [number, number, number]),
    [positions],
  );
  if (pts.length < 2) return null;
  return <Line points={pts} color={color} lineWidth={2} />;
}

function Marker({
  position,
  color,
  label,
}: {
  position: [number, number, number];
  color: string;
  label: string;
}) {
  return (
    <group position={position}>
      <mesh>
        <sphereGeometry args={[0.03, 16, 16]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.5} />
      </mesh>
      <Html distanceFactor={5} style={{ pointerEvents: "none" }}>
        <span
          style={{
            color,
            fontSize: "10px",
            fontFamily: "JetBrains Mono, monospace",
            whiteSpace: "nowrap",
            textShadow: "0 0 4px #000",
          }}
        >
          {label}
        </span>
      </Html>
    </group>
  );
}

function ShipMarker({ interpolated }: { interpolated: InterpolatedState }) {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame(() => {
    if (meshRef.current) {
      meshRef.current.position.set(
        interpolated.positionAU[0],
        interpolated.positionAU[1],
        interpolated.positionAU[2],
      );
    }
  });

  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[0.04, 16, 16]} />
      <meshStandardMaterial
        color="#f59e0b"
        emissive="#f59e0b"
        emissiveIntensity={1.5}
      />
    </mesh>
  );
}

function EarthMarker({ interpolated }: { interpolated: InterpolatedState }) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame(() => {
    if (groupRef.current) {
      groupRef.current.position.set(
        interpolated.earthPositionAU[0],
        interpolated.earthPositionAU[1],
        interpolated.earthPositionAU[2],
      );
    }
  });

  return (
    <group ref={groupRef}>
      <RealisticEarth radius={0.03} />
    </group>
  );
}

function Scene({ worldline, earth, interpolated, targetTrajectory }: Props) {
  const shipPosAU = worldline.positions_au;

  const len = shipPosAU.length;
  const midIdx = Math.floor(len / 2);
  const first = shipPosAU[0]!;
  const mid = shipPosAU[midIdx]!;
  const last = shipPosAU[len - 1]!;

  const departure: [number, number, number] = [first[0]!, first[1]!, first[2]!];
  const turnaround: [number, number, number] = [mid[0]!, mid[1]!, mid[2]!];
  const arrival: [number, number, number] = [last[0]!, last[1]!, last[2]!];

  const targetColor = targetTrajectory
    ? TARGET_COLORS[targetTrajectory.name] ?? "#a855f7"
    : null;

  const maxRadius = targetTrajectory
    ? Math.max(1, targetTrajectory.orbit_radius_au)
    : 1;

  return (
    <>
      <ambientLight intensity={0.3} />

      {/* Sun at origin */}
      <group position={[0, 0, 0]}>
        <RealisticSun radius={0.06} />
      </group>

      {/* Grid on ecliptic */}
      <gridHelper
        args={[maxRadius * 4, 30, "#27272a", "#18181b"]}
        rotation={[Math.PI / 2, 0, 0] as unknown as THREE.Euler}
      />

      {/* Earth orbit ring (1 AU) */}
      <OrbitRing radius={1} color="#3b82f6" />

      {/* Target orbit ring (if different from Earth) */}
      {targetTrajectory && targetColor && (
        <OrbitRing radius={targetTrajectory.orbit_radius_au} color={targetColor} />
      )}

      {/* Earth trajectory */}
      <TrajectoryLine positions={earth.trajectory_positions_au} color="#3b82f6" />

      {/* Target trajectory */}
      {targetTrajectory && targetColor && (
        <TrajectoryLine positions={targetTrajectory.trajectory_positions_au} color={targetColor} />
      )}

      {/* Ship trajectory */}
      <TrajectoryLine positions={shipPosAU} color="#ef4444" />

      <Marker position={departure} color="#22c55e" label="DEP" />
      <Marker position={turnaround} color="#ef4444" label="TURN" />
      <Marker position={arrival} color="#06b6d4" label="ARR" />

      {/* Target arrival marker */}
      {targetTrajectory && targetColor && (
        <Marker
          position={[
            targetTrajectory.arrival_position_au[0]!,
            targetTrajectory.arrival_position_au[1]!,
            targetTrajectory.arrival_position_au[2]!,
          ]}
          color={targetColor}
          label={targetTrajectory.name.toUpperCase()}
        />
      )}

      {/* Animated markers */}
      {interpolated && <ShipMarker interpolated={interpolated} />}
      {interpolated && <EarthMarker interpolated={interpolated} />}

      <OrbitControls
        makeDefault
        enableDamping
        dampingFactor={0.1}
        minDistance={0.5}
        maxDistance={20}
      />
    </>
  );
}

export function OrbitalView({ worldline, earth, interpolated, targetTrajectory }: Props) {
  return (
    <Canvas
      camera={{ position: [0, 0, 3], fov: 50, near: 0.01, far: 100 }}
      style={{ background: "#09090b" }}
    >
      <Suspense fallback={null}>
        <Scene
          worldline={worldline}
          earth={earth}
          interpolated={interpolated}
          targetTrajectory={targetTrajectory}
        />
      </Suspense>
    </Canvas>
  );
}
