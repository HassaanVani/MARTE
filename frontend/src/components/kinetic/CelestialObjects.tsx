import { Html } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import type { InterpolatedState } from "../../types";
import { GhostEarth, RealisticEarth, RealisticSun } from "../celestial/Bodies";

interface Props {
  interpolated: InterpolatedState | null;
}

const AU_SCALE = 10;

function EngineGlow({ interpolated }: Props) {
  const meshRef = useRef<THREE.Mesh>(null);
  const lightRef = useRef<THREE.PointLight>(null);

  useFrame(() => {
    if (!interpolated || !meshRef.current || !lightRef.current) return;

    const vDir = interpolated.velocityDirection;
    const isThrusting =
      interpolated.phase === "ACCELERATING" || interpolated.phase === "DECELERATING";
    const intensity = isThrusting ? 0.5 + interpolated.beta * 2.0 : 0;

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

  useFrame(() => {
    if (!interpolated || !groupRef.current) return;
    const shipPos = interpolated.positionAU;
    groupRef.current.position.set(
      -shipPos[0] * AU_SCALE,
      -shipPos[1] * AU_SCALE,
      -shipPos[2] * AU_SCALE,
    );
  });

  return (
    <group ref={groupRef}>
      <RealisticSun radius={0.6} />
    </group>
  );
}

/** Faint ring showing Earth's orbital path around the Sun */
function OrbitTrace({ interpolated }: Props) {
  const ringRef = useRef<THREE.Mesh>(null);

  useFrame(() => {
    if (!interpolated || !ringRef.current) return;
    const shipPos = interpolated.positionAU;
    ringRef.current.position.set(
      -shipPos[0] * AU_SCALE,
      -shipPos[1] * AU_SCALE,
      -shipPos[2] * AU_SCALE,
    );
  });

  return (
    <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]}>
      <ringGeometry args={[AU_SCALE * 0.98, AU_SCALE * 1.02, 128]} />
      <meshBasicMaterial
        color="#3b82f6"
        transparent
        opacity={0.08}
        side={THREE.DoubleSide}
      />
    </mesh>
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
      <RealisticEarth radius={0.2} />
      {/* Label */}
      <Html
        center
        distanceFactor={15}
        style={{ pointerEvents: "none", userSelect: "none" }}
      >
        <div style={{
          color: "#60a5fa",
          fontSize: "9px",
          fontFamily: "'JetBrains Mono', monospace",
          letterSpacing: "0.15em",
          textTransform: "uppercase",
          whiteSpace: "nowrap",
          textShadow: "0 0 4px rgba(59,130,246,0.5)",
          marginTop: "-28px",
        }}>
          EARTH
          <span style={{ opacity: 0.5, marginLeft: "6px" }}>
            {interpolated ? `${interpolated.distanceToEarth.toFixed(2)} AU` : ""}
          </span>
        </div>
      </Html>
    </group>
  );
}

function EarthGhostWithLabel({ interpolated }: Props) {
  const groupRef = useRef<THREE.Group>(null);
  const lineObjRef = useRef<THREE.Line | null>(null);

  const lineMat = useMemo(
    () =>
      new THREE.LineDashedMaterial({
        color: "#6699ff",
        dashSize: 0.3,
        gapSize: 0.2,
        transparent: true,
        opacity: 0.3,
      }),
    [],
  );

  const lineObj = useMemo(() => {
    const geom = new THREE.BufferGeometry();
    geom.setAttribute(
      "position",
      new THREE.Float32BufferAttribute([0, 0, 0, 0, 0, 0], 3),
    );
    const obj = new THREE.Line(geom, lineMat);
    lineObjRef.current = obj;
    return obj;
  }, [lineMat]);

  useFrame(() => {
    if (!interpolated || !groupRef.current || !lineObjRef.current) return;
    const shipPos = interpolated.positionAU;
    const apparentPos = interpolated.earthApparentPositionAU;
    const actualPos = interpolated.earthPositionAU;

    groupRef.current.position.set(
      (apparentPos[0] - shipPos[0]) * AU_SCALE,
      (apparentPos[1] - shipPos[1]) * AU_SCALE,
      (apparentPos[2] - shipPos[2]) * AU_SCALE,
    );

    const geom = lineObjRef.current.geometry as THREE.BufferGeometry;
    const positions = geom.attributes.position;
    if (positions) {
      positions.setXYZ(
        0,
        (actualPos[0] - shipPos[0]) * AU_SCALE,
        (actualPos[1] - shipPos[1]) * AU_SCALE,
        (actualPos[2] - shipPos[2]) * AU_SCALE,
      );
      positions.setXYZ(
        1,
        (apparentPos[0] - shipPos[0]) * AU_SCALE,
        (apparentPos[1] - shipPos[1]) * AU_SCALE,
        (apparentPos[2] - shipPos[2]) * AU_SCALE,
      );
      positions.needsUpdate = true;
      lineObjRef.current.computeLineDistances();
    }
  });

  return (
    <>
      <group ref={groupRef}>
        <GhostEarth radius={0.18} />
        {/* TARGET label */}
        <Html
          center
          distanceFactor={15}
          style={{ pointerEvents: "none", userSelect: "none" }}
        >
          <div style={{
            color: "#f59e0b",
            fontSize: "9px",
            fontFamily: "'JetBrains Mono', monospace",
            letterSpacing: "0.2em",
            textTransform: "uppercase",
            whiteSpace: "nowrap",
            textShadow: "0 0 6px rgba(245,158,11,0.4)",
            marginTop: "-24px",
            textAlign: "center",
          }}>
            ◇ TARGET
            <div style={{ fontSize: "8px", color: "#f59e0b80", marginTop: "1px" }}>
              AIM HERE
            </div>
          </div>
        </Html>
      </group>
      <primitive object={lineObj} />
    </>
  );
}

export function CelestialObjects({ interpolated }: Props) {
  return (
    <>
      <Sun interpolated={interpolated} />
      <OrbitTrace interpolated={interpolated} />
      <Earth interpolated={interpolated} />
      <EarthGhostWithLabel interpolated={interpolated} />
      <EngineGlow interpolated={interpolated} />
    </>
  );
}
