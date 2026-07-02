"use client";
import { useRef, useMemo, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Stars, Sparkles, Sphere, Torus } from "@react-three/drei";
import * as THREE from "three";
import { useAppStore } from "@/store/useAppStore";
import { useVoiceStore } from "@/store/useVoiceStore";

function AI_Core() {
  const coreRef = useRef<THREE.Group>(null);
  const ring1Ref = useRef<THREE.Mesh>(null);
  const ring2Ref = useRef<THREE.Mesh>(null);
  const ring3Ref = useRef<THREE.Mesh>(null);

  const innerCoreMaterialRef = useRef<THREE.MeshStandardMaterial>(null);

  const { state: voiceState, audioLevel } = useVoiceStore();

  const targetColor = useMemo(() => new THREE.Color(), []);

  useFrame((state, delta) => {
    if (!coreRef.current) return;

    let rotSpeedX = 0.1;
    let rotSpeedY = 0.2;
    let targetScale = 1;

    if (voiceState === 'listening') {
      targetScale = 1.2;
      targetColor.setHex(0x00ffff);
    } else if (voiceState === 'thinking') {
      rotSpeedX = 0.5;
      rotSpeedY = 1.0;
      targetScale = 0.9;
      targetColor.setHex(0xff00ff);
    } else if (voiceState === 'speaking') {
      targetScale = 1.1 + (audioLevel * 0.3);
      targetColor.setHex(0x00ff88);
    } else {
      targetScale = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.02;
      targetColor.setHex(0x0066ff);
    }

    coreRef.current.rotation.y += delta * rotSpeedY;
    coreRef.current.rotation.x += delta * rotSpeedX;

    coreRef.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.1);

    if (innerCoreMaterialRef.current) {
      innerCoreMaterialRef.current.color.lerp(targetColor, 0.05);
      innerCoreMaterialRef.current.emissive.lerp(targetColor, 0.05);

      if (voiceState === 'speaking') {
        innerCoreMaterialRef.current.emissiveIntensity = 2 + (audioLevel * 3);
      } else if (voiceState === 'thinking') {
        innerCoreMaterialRef.current.emissiveIntensity = 1 + Math.sin(state.clock.elapsedTime * 10) * 0.5;
      } else {
        innerCoreMaterialRef.current.emissiveIntensity = 2;
      }
    }

    if (ring1Ref.current) {
      ring1Ref.current.rotation.x += delta * (voiceState === 'thinking' ? 1.5 : 0.5);
      ring1Ref.current.rotation.y -= delta * (voiceState === 'listening' ? 1.0 : 0.3);
      const ringScale = voiceState === 'listening' ? 1.1 + Math.sin(state.clock.elapsedTime * 5) * 0.05 : 1;
      ring1Ref.current.scale.lerp(new THREE.Vector3(ringScale, ringScale, ringScale), 0.1);
    }
    if (ring2Ref.current) {
      ring2Ref.current.rotation.y += delta * (voiceState === 'thinking' ? 1.8 : 0.6);
      ring2Ref.current.rotation.z += delta * 0.2;
    }
    if (ring3Ref.current) {
      ring3Ref.current.rotation.x -= delta * 0.4;
      ring3Ref.current.rotation.z -= delta * (voiceState === 'speaking' ? 1.0 : 0.5);
    }
  });

  return (
    <group ref={coreRef}>
      <Sphere args={[1.5, 64, 64]}>
        <meshStandardMaterial
          ref={innerCoreMaterialRef}
          color="#0066ff"
          emissive="#0044ff"
          emissiveIntensity={2}
          wireframe
          transparent
          opacity={0.8}
        />
      </Sphere>

      <Sphere args={[1.7, 32, 32]}>
        <meshStandardMaterial
          color="#44aaff"
          emissive="#0088ff"
          emissiveIntensity={0.5}
          transparent
          opacity={0.15}
          depthWrite={false}
        />
      </Sphere>

      <Torus ref={ring1Ref} args={[2.5, 0.02, 16, 100]} rotation={[Math.PI / 4, 0, 0]}>
        <meshStandardMaterial color="#00ffff" emissive="#00ffff" emissiveIntensity={2} />
      </Torus>

      <Torus ref={ring2Ref} args={[3.5, 0.01, 16, 100]} rotation={[0, Math.PI / 3, 0]}>
        <meshStandardMaterial color="#0088ff" emissive="#0088ff" emissiveIntensity={1.5} />
      </Torus>

      <Torus ref={ring3Ref} args={[4.5, 0.03, 16, 100]} rotation={[0, 0, Math.PI / 6]}>
        <meshStandardMaterial color="#ffffff" emissive="#ffffff" emissiveIntensity={1} transparent opacity={0.3}/>
      </Torus>

      <Sparkles count={200} scale={5} size={2} speed={0.4} opacity={0.5} color="#00ffff" />
    </group>
  );
}

function CameraRig() {
  useFrame((state) => {
    const targetX = (state.pointer.x * 2);
    const targetY = (state.pointer.y * 2);

    state.camera.position.x += (targetX - state.camera.position.x) * 0.05;
    state.camera.position.y += (targetY - state.camera.position.y) * 0.05;
    state.camera.lookAt(0, 0, 0);
  });
  return null;
}

export function AICoreScene() {
  const [isReady, setIsReady] = useState(false);

  return (
    <div className="absolute inset-0 z-0 bg-black overflow-hidden pointer-events-auto">
      {!isReady && (
        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-black">
          <div className="w-10 h-10 rounded-full border-2 border-blue-500/30 border-t-blue-400 animate-spin" />
          <p className="mt-4 text-xs tracking-[0.3em] text-blue-300/70 uppercase">Initializing core</p>
        </div>
      )}
      <Canvas
        camera={{ position: [0, 0, 10], fov: 45 }}
        onCreated={() => setIsReady(true)}
      >
        <color attach="background" args={["#000005"]} />
        <fog attach="fog" args={["#000005", 5, 20]} />

        <ambientLight intensity={0.2} />
        <pointLight position={[10, 10, 10]} intensity={1} color="#0066ff" />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#0022ff" />

        <AI_Core />
        <CameraRig />

        <Stars radius={100} depth={50} count={1500} factor={4} saturation={0} fade speed={1} />
        <Sparkles count={150} scale={20} size={1} speed={0.1} opacity={0.2} color="#ffffff" />
      </Canvas>
    </div>
  );
}
