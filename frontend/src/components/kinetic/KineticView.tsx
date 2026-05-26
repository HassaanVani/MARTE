import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Suspense, useEffect, useRef } from "react";
import * as THREE from "three";
import type { AnimationControls } from "../../hooks/useAnimationState";
import type { InterpolatedState, SolveResponse } from "../../types";
import { CelestialObjects } from "./CelestialObjects";
import { CockpitHUD } from "./CockpitHUD";
import { CockpitTimeline } from "./CockpitTimeline";
import { RelativisticStarfield } from "./RelativisticStarfield";

interface Props {
  response: SolveResponse;
  interpolated: InterpolatedState | null;
  animation: AnimationControls;
}

function CameraController({
  interpolated,
}: {
  interpolated: InterpolatedState | null;
}) {
  const { gl, camera } = useThree();
  const targetQuaternion = useRef(new THREE.Quaternion());
  const currentQuaternion = useRef(new THREE.Quaternion());
  const initialized = useRef(false);

  // Mouse drag offsets
  const yaw = useRef(0);
  const pitch = useRef(0);
  const targetCenterDir = useRef<[number, number, number] | null>(null);

  useEffect(() => {
    let isDragging = false;
    let prevX = 0;
    let prevY = 0;

    const onPointerDown = (e: PointerEvent) => {
      isDragging = true;
      prevX = e.clientX;
      prevY = e.clientY;
      gl.domElement.style.cursor = "grabbing";
    };

    const onPointerMove = (e: PointerEvent) => {
      if (!isDragging) return;
      const dx = e.clientX - prevX;
      const dy = e.clientY - prevY;
      yaw.current -= dx * 0.003;
      pitch.current -= dy * 0.003;
      // Clamp pitch to avoid flipping over
      pitch.current = Math.max(-Math.PI / 2 + 0.1, Math.min(Math.PI / 2 - 0.1, pitch.current));
      prevX = e.clientX;
      prevY = e.clientY;
    };

    const onPointerUp = () => {
      isDragging = false;
      gl.domElement.style.cursor = "grab";
    };

    const onDoubleClick = () => {
      yaw.current = 0;
      pitch.current = 0;
    };

    const onCenterTarget = (e: any) => {
      targetCenterDir.current = e.detail;
    };

    gl.domElement.style.cursor = "grab";
    gl.domElement.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    gl.domElement.addEventListener("dblclick", onDoubleClick);
    window.addEventListener("marte-center-target", onCenterTarget);

    return () => {
      gl.domElement.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      gl.domElement.removeEventListener("dblclick", onDoubleClick);
      window.removeEventListener("marte-center-target", onCenterTarget);
    };
  }, [gl.domElement]);

  useFrame(() => {
    if (!interpolated) return;

    const dir = new THREE.Vector3(
      interpolated.velocityDirection[0],
      interpolated.velocityDirection[1],
      interpolated.velocityDirection[2],
    ).normalize();

    const lookAtMatrix = new THREE.Matrix4();
    const up = new THREE.Vector3(0, 0, 1);
    if (Math.abs(dir.dot(up)) > 0.99) {
      up.set(0, 1, 0);
    }
    lookAtMatrix.lookAt(new THREE.Vector3(0, 0, 0), dir, up);
    
    // Base flight direction
    const baseQuat = new THREE.Quaternion().setFromRotationMatrix(lookAtMatrix);

    if (targetCenterDir.current) {
      const tDir = new THREE.Vector3(...targetCenterDir.current).normalize();
      const tLookAt = new THREE.Matrix4();
      const tUp = new THREE.Vector3(0, 0, 1);
      if (Math.abs(tDir.dot(tUp)) > 0.99) tUp.set(0, 1, 0);
      tLookAt.lookAt(new THREE.Vector3(0, 0, 0), tDir, tUp);
      
      const tQuat = new THREE.Quaternion().setFromRotationMatrix(tLookAt);
      const invBase = baseQuat.clone().invert();
      const userOffset = invBase.multiply(tQuat);
      
      const euler = new THREE.Euler().setFromQuaternion(userOffset, "YXZ");
      yaw.current = euler.y;
      pitch.current = euler.x;
      targetCenterDir.current = null;
    }
    
    // Apply user look offset
    const userOffset = new THREE.Quaternion().setFromEuler(
      new THREE.Euler(pitch.current, yaw.current, 0, "YXZ")
    );
    targetQuaternion.current.copy(baseQuat).multiply(userOffset);

    if (!initialized.current) {
      currentQuaternion.current.copy(targetQuaternion.current);
      initialized.current = true;
    } else {
      currentQuaternion.current.slerp(targetQuaternion.current, 0.1);
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

export function KineticView({ interpolated, animation }: Props) {
  return (
    <div className="relative h-full w-full">
      <Canvas
        camera={{ fov: 75, near: 0.01, far: 1e10, position: [0, 0, 0] }}
        gl={{ logarithmicDepthBuffer: true }}
        style={{ background: "#000000" }}
      >
        <Suspense fallback={null}>
          <KineticScene interpolated={interpolated} />
        </Suspense>
      </Canvas>
      <CockpitHUD interpolated={interpolated} />
      <CockpitTimeline animation={animation} interpolated={interpolated} />
      
      {/* Help Overlay */}
      <div className="pointer-events-none absolute top-4 left-1/2 -translate-x-1/2 text-center text-[10px] uppercase tracking-widest text-text-dim opacity-50">
        Drag to look around • Double click to center
      </div>
    </div>
  );
}
