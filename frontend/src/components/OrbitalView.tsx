import { Html, Line, OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useMemo } from "react";
import type * as THREE from "three";
import type { EarthData, WorldlineData } from "../types";

interface Props {
  worldline: WorldlineData;
  earth: EarthData;
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

function Scene({ worldline, earth }: Props) {
  const shipPosAU = worldline.positions_au;
  const earthPosAU = earth.trajectory_positions_au;

  const departure: [number, number, number] = [
    shipPosAU[0]![0]!, shipPosAU[0]![1]!, shipPosAU[0]![2]!,
  ];
  const turnaround: [number, number, number] = [
    shipPosAU[1]![0]!, shipPosAU[1]![1]!, shipPosAU[1]![2]!,
  ];
  const arrival: [number, number, number] = [
    shipPosAU[2]![0]!, shipPosAU[2]![1]!, shipPosAU[2]![2]!,
  ];

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

export function OrbitalView({ worldline, earth }: Props) {
  return (
    <Canvas
      camera={{ position: [0, 0, 3], fov: 50, near: 0.01, far: 100 }}
      style={{ background: "#09090b" }}
    >
      <Scene worldline={worldline} earth={earth} />
    </Canvas>
  );
}
