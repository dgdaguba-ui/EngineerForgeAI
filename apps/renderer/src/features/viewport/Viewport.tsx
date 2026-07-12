/**
 * The 3D viewport — react-three-fiber scene with orbit controls, grid,
 * lighting, and click-to-select on loaded meshes.
 */
import { OrbitControls } from "@react-three/drei";
import { Canvas, useThree } from "@react-three/fiber";
import { useEffect, useMemo } from "react";
import { BoxGeometry, EdgesGeometry, Vector3 } from "three";

/** Minimal orbit-controls surface used by the camera fit (avoids a direct three-stdlib dep). */
interface OrbitControlsLike {
  target: Vector3;
  update: () => void;
}

import {
  combinedBoundingBox,
  useViewportStore,
  type SceneObject,
} from "../../state/viewportStore";

function SceneMesh({ object }: { object: SceneObject }) {
  const selectedId = useViewportStore((s) => s.selectedId);
  const select = useViewportStore((s) => s.select);
  const selected = selectedId === object.id;

  if (!object.visible) return null;
  return (
    <mesh
      geometry={object.geometry}
      onClick={(e) => {
        e.stopPropagation();
        select(object.id);
      }}
    >
      <meshStandardMaterial
        color={object.color}
        metalness={0.1}
        roughness={0.65}
        emissive={selected ? "#22d3ee" : "#000000"}
        emissiveIntensity={selected ? 0.3 : 0}
      />
    </mesh>
  );
}

/** Re-fits the camera and orbit target whenever scene content changes. */
function FitCamera() {
  const camera = useThree((s) => s.camera);
  const controls = useThree((s) => s.controls) as OrbitControlsLike | null;
  const objects = useViewportStore((s) => s.objects);
  const contentVersion = useViewportStore((s) => s.contentVersion);

  useEffect(() => {
    const box = combinedBoundingBox(objects);
    if (!box) return;
    const center = box.getCenter(new Vector3());
    const size = box.getSize(new Vector3());
    const maxDim = Math.max(size.x, size.y, size.z, 1);
    const dist = maxDim * 1.9 + 15;
    camera.position.set(center.x + dist, center.y + dist * 0.72, center.z + dist);
    if ("far" in camera) {
      camera.far = Math.max(5000, dist * 20);
      camera.updateProjectionMatrix();
    }
    if (controls) {
      controls.target.copy(center);
      controls.update();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contentVersion]);

  return null;
}

/** Wireframe of the active printer's build volume (printer Z = world Y up). */
function BuildVolumeBox() {
  const buildVolume = useViewportStore((s) => s.buildVolume);
  const edges = useMemo(() => {
    if (!buildVolume) return null;
    const box = new BoxGeometry(buildVolume.x, buildVolume.z, buildVolume.y);
    const geometry = new EdgesGeometry(box);
    box.dispose();
    return geometry;
  }, [buildVolume]);

  if (!buildVolume || !edges) return null;
  return (
    <lineSegments geometry={edges} position={[0, buildVolume.z / 2, 0]}>
      <lineBasicMaterial color="#155e6e" />
    </lineSegments>
  );
}

export function Viewport() {
  const objects = useViewportStore((s) => s.objects);
  const select = useViewportStore((s) => s.select);
  const buildVolume = useViewportStore((s) => s.buildVolume);
  const gridColors = useMemo(() => ({ major: "#3f3f46", minor: "#232327" }), []);
  const gridSize = buildVolume ? Math.max(buildVolume.x, buildVolume.y) : 220;

  return (
    <div className="relative h-full w-full" data-testid="viewport">
      <Canvas
        dpr={[1, 2]}
        camera={{ position: [140, 105, 140], fov: 45, near: 0.1, far: 5000 }}
        onPointerMissed={() => select(null)}
        gl={{ antialias: true }}
        style={{ background: "#0c0c0f" }}
      >
        <ambientLight intensity={0.45} />
        <hemisphereLight args={["#b8c4d4", "#1a1a1e", 0.5]} />
        <directionalLight position={[80, 140, 60]} intensity={1.1} />
        <directionalLight position={[-60, 40, -80]} intensity={0.3} />

        {/* bed grid sized to the active printer (10mm cells) */}
        <gridHelper
          args={[gridSize, Math.round(gridSize / 10), gridColors.major, gridColors.minor]}
        />
        <axesHelper args={[30]} />
        <BuildVolumeBox />

        {objects.map((o) => (
          <SceneMesh key={o.id} object={o} />
        ))}

        <OrbitControls makeDefault enableDamping dampingFactor={0.1} />
        <FitCamera />
      </Canvas>
      {objects.length === 0 && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <p className="text-sm text-zinc-600">
            Import an STL from the Scene panel to get started
          </p>
        </div>
      )}
    </div>
  );
}
