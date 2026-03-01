import { Html, Line, OrbitControls } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import type { EarthData, InterpolatedState, WorldlineData } from "../types";

interface Props {
  worldline: WorldlineData;
  earth: EarthData;
  interpolated: InterpolatedState | null;
}

function EarthOrbitRing() {
  const points = useMemo(() => {
    const pts: [number, number, number][] = [];
    for (let i = 0; i <= 360; i++) {
      const a = (i * Math.PI) / 180;
      pts.push([Math.cos(a), Math.sin(a), 0]);
    }
    return pts;
  }, []);
  return <Line points={points} color="#3b82f6" lineWidth={1} dashed dashScale={40} dashSize={1} gapSize={1} />;
}

function EarthTrajectory({ positions }: { positions: number[][] }) {
  const pts = useMemo(
    () => positions.map((p) => [p[0]!, p[1]!, p[2]!] as [number, number, number]),
    [positions],
  );
  if (pts.length < 2) return null;
  return <Line points={pts} color="#3b82f6" lineWidth={2} />;
}

function ShipTrajectory({ positions }: { positions: number[][] }) {
  const pts = useMemo(
    () => positions.map((p) => [p[0]!, p[1]!, p[2]!] as [number, number, number]),
    [positions],
  );
  if (pts.length < 2) return null;
  return <Line points={pts} color="#ef4444" lineWidth={2} />;
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
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame(() => {
    if (meshRef.current) {
      meshRef.current.position.set(
        interpolated.earthPositionAU[0],
        interpolated.earthPositionAU[1],
        interpolated.earthPositionAU[2],
      );
    }
  });

  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[0.025, 16, 16]} />
      <meshStandardMaterial
        color="#3b82f6"
        emissive="#3b82f6"
        emissiveIntensity={1}
      />
    </mesh>
  );
}

function Scene({ worldline, earth, interpolated }: Props) {
  const shipPosAU = worldline.positions_au;
  const earthPosAU = earth.trajectory_positions_au;

  const len = shipPosAU.length;
  const midIdx = Math.floor(len / 2);
  const first = shipPosAU[0]!;
  const mid = shipPosAU[midIdx]!;
  const last = shipPosAU[len - 1]!;

  const departure: [number, number, number] = [first[0]!, first[1]!, first[2]!];
  const turnaround: [number, number, number] = [mid[0]!, mid[1]!, mid[2]!];
  const arrival: [number, number, number] = [last[0]!, last[1]!, last[2]!];

  return (
    <>
      <ambientLight intensity={0.3} />
      <pointLight position={[0, 0, 0]} intensity={2} color="#fbbf24" />

      {/* Sun */}
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[0.05, 32, 32]} />
        <meshStandardMaterial
          color="#fbbf24"
          emissive="#fbbf24"
          emissiveIntensity={2}
        />
      </mesh>

      {/* Grid on ecliptic */}
      <gridHelper
        args={[6, 30, "#27272a", "#18181b"]}
        rotation={[Math.PI / 2, 0, 0] as unknown as THREE.Euler}
      />

      <EarthOrbitRing />
      <EarthTrajectory positions={earthPosAU} />
      <ShipTrajectory positions={shipPosAU} />

      <Marker position={departure} color="#22c55e" label="DEP" />
      <Marker position={turnaround} color="#ef4444" label="TURN" />
      <Marker position={arrival} color="#06b6d4" label="ARR" />

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

export function OrbitalView({ worldline, earth, interpolated }: Props) {
  return (
    <Canvas
      camera={{ position: [0, 0, 3], fov: 50, near: 0.01, far: 100 }}
      style={{ background: "#09090b" }}
    >
      <Scene worldline={worldline} earth={earth} interpolated={interpolated} />
    </Canvas>
  );
}
