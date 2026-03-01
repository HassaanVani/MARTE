import { Canvas, useFrame } from "@react-three/fiber";
import { useRef } from "react";
import * as THREE from "three";
import type { InterpolatedState, SolveResponse } from "../../types";
import { CelestialObjects } from "./CelestialObjects";
import { CockpitHUD } from "./CockpitHUD";
import { RelativisticStarfield } from "./RelativisticStarfield";

interface Props {
  response: SolveResponse;
  interpolated: InterpolatedState | null;
}

function CameraController({
  interpolated,
}: {
  interpolated: InterpolatedState | null;
}) {
  const targetQuaternion = useRef(new THREE.Quaternion());
  const currentQuaternion = useRef(new THREE.Quaternion());
  const initialized = useRef(false);

  useFrame(({ camera }) => {
    if (!interpolated) return;

    const dir = new THREE.Vector3(
      interpolated.velocityDirection[0],
      interpolated.velocityDirection[1],
      interpolated.velocityDirection[2],
    ).normalize();

    // Create a look-at quaternion for the velocity direction
    const lookAtMatrix = new THREE.Matrix4();
    const up = new THREE.Vector3(0, 0, 1);
    // If velocity is nearly parallel to up, use a different up vector
    if (Math.abs(dir.dot(up)) > 0.99) {
      up.set(0, 1, 0);
    }
    lookAtMatrix.lookAt(new THREE.Vector3(0, 0, 0), dir, up);
    targetQuaternion.current.setFromRotationMatrix(lookAtMatrix);

    if (!initialized.current) {
      currentQuaternion.current.copy(targetQuaternion.current);
      initialized.current = true;
    } else {
      // Smooth slerp to prevent snapping at turnaround
      currentQuaternion.current.slerp(targetQuaternion.current, 0.05);
    }

    camera.quaternion.copy(currentQuaternion.current);
  });

  return null;
}

function KineticScene({ interpolated }: { interpolated: InterpolatedState | null }) {
  return (
    <>
      <ambientLight intensity={0.1} />
      <CameraController interpolated={interpolated} />
      <RelativisticStarfield interpolated={interpolated} />
      <CelestialObjects interpolated={interpolated} />
    </>
  );
}

export function KineticView({ interpolated }: Props) {
  return (
    <div className="relative h-full w-full">
      <Canvas
        camera={{ fov: 75, near: 0.01, far: 2000, position: [0, 0, 0] }}
        style={{ background: "#000000" }}
      >
        <KineticScene interpolated={interpolated} />
      </Canvas>
      <CockpitHUD interpolated={interpolated} />
    </div>
  );
}
