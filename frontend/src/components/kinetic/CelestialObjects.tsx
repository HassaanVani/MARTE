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
    
    let dx = -shipPos[0] * AU_SCALE;
    let dy = -shipPos[1] * AU_SCALE;
    let dz = -shipPos[2] * AU_SCALE;
    
    // Prevent clipping inside Sun (radius ~0.6)
    const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
    if (dist < 1.0) {
      if (dist < 0.0001) { dz = -1.0; }
      else { const scale = 1.0 / dist; dx *= scale; dy *= scale; dz *= scale; }
    }
    
    groupRef.current.position.set(dx, dy, dz);
  });

  return (
    <group ref={groupRef}>
      <RealisticSun radius={0.6} />
    </group>
  );
}

const PLANETS = [
  { name: "Mercury", radiusAU: 0.39, size: 0.08, color: "#8c8c8c", period: 0.24 },
  { name: "Venus", radiusAU: 0.72, size: 0.19, color: "#e3bb76", period: 0.62 },
  { name: "Mars", radiusAU: 1.52, size: 0.1, color: "#c1440e", period: 1.88 },
  { name: "Jupiter", radiusAU: 5.20, size: 0.5, color: "#d39c7e", period: 11.86 },
  { name: "Saturn", radiusAU: 9.54, size: 0.4, color: "#ead6b8", period: 29.46 },
  { name: "Uranus", radiusAU: 19.2, size: 0.25, color: "#4b70dd", period: 84.01 },
  { name: "Neptune", radiusAU: 30.06, size: 0.24, color: "#415bb3", period: 164.8 },
];

function SolarSystemPlanets({ interpolated }: Props) {
  const groupRef = useRef<THREE.Group>(null);
  
  useFrame(() => {
    if (!interpolated || !groupRef.current) return;
    const shipPos = interpolated.positionAU;
    const t = interpolated.coordTime; // in years
    
    // Sun position
    let dx = -shipPos[0] * AU_SCALE;
    let dy = -shipPos[1] * AU_SCALE;
    let dz = -shipPos[2] * AU_SCALE;
    
    groupRef.current.position.set(dx, dy, dz);
    
    // Update planets
    groupRef.current.children.forEach((child) => {
      if (child.userData.planetIndex !== undefined) {
         const idx = child.userData.planetIndex as number;
         const p = PLANETS[idx];
         if (p) {
           const theta = (t / p.period) * Math.PI * 2 + (idx * 2.3);
           child.position.set(
             p.radiusAU * Math.cos(theta) * AU_SCALE,
             p.radiusAU * Math.sin(theta) * AU_SCALE,
             0
           );
         }
      }
    });
  });

  return (
    <group ref={groupRef}>
      {PLANETS.map((p, i) => (
        <mesh key={p.name} userData={{ planetIndex: i }}>
          <sphereGeometry args={[p.size, 32, 32]} />
          <meshStandardMaterial color={p.color} roughness={0.7} />
          {p.name === "Saturn" && (
             <mesh rotation={[Math.PI / 2 + 0.2, 0, 0]}>
               <ringGeometry args={[p.size * 1.4, p.size * 2.2, 64]} />
               <meshBasicMaterial color="#d8c5a2" transparent opacity={0.6} side={THREE.DoubleSide} />
             </mesh>
          )}
          <Html center distanceFactor={15} style={{ pointerEvents: "none", userSelect: "none" }}>
            <div style={{ color: p.color, fontSize: "8px", fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.15em", textTransform: "uppercase", whiteSpace: "nowrap", opacity: 0.6, marginTop: "-20px" }}>
              {p.name}
            </div>
          </Html>
        </mesh>
      ))}
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
    
    let dx = (earthPos[0] - shipPos[0]) * AU_SCALE;
    let dy = (earthPos[1] - shipPos[1]) * AU_SCALE;
    let dz = (earthPos[2] - shipPos[2]) * AU_SCALE;

    // Prevent clipping inside Earth (radius 0.2)
    const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
    if (dist < 0.4) {
      if (dist < 0.0001) { dz = -0.4; }
      else { const scale = 0.4 / dist; dx *= scale; dy *= scale; dz *= scale; }
    }

    groupRef.current.position.set(dx, dy, dz);
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

function TargetGhostWithLabel({ interpolated }: Props) {
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
    const apparentPos = interpolated.targetApparentPositionAU;
    const actualPos = interpolated.targetPositionAU;

    let dxApp = (apparentPos[0] - shipPos[0]) * AU_SCALE;
    let dyApp = (apparentPos[1] - shipPos[1]) * AU_SCALE;
    let dzApp = (apparentPos[2] - shipPos[2]) * AU_SCALE;

    // Prevent clipping
    const distApp = Math.sqrt(dxApp * dxApp + dyApp * dyApp + dzApp * dzApp);
    if (distApp < 0.4) {
      if (distApp < 0.0001) { dzApp = -0.4; }
      else { const scale = 0.4 / distApp; dxApp *= scale; dyApp *= scale; dzApp *= scale; }
    }

    groupRef.current.position.set(dxApp, dyApp, dzApp);

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
    <group>
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
    </group>
  );
}

export function CelestialObjects({ interpolated }: Props) {
  return (
    <>
      <Sun interpolated={interpolated} />
      <SolarSystemPlanets interpolated={interpolated} />
      <OrbitTrace interpolated={interpolated} />
      <Earth interpolated={interpolated} />
      <TargetGhostWithLabel interpolated={interpolated} />
      <EngineGlow interpolated={interpolated} />
    </>
  );
}
