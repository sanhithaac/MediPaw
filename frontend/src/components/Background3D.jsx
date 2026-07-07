import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import './Background3D.css';
import {
  CAMERA,
  ICONS,
  LIGHT_RAYS,
  MOUSE,
  FOG,
  ANIMATION,
  WORLD,
  THREE_COLORS,
} from './constants';
import {
  createParticleSystem,
  updateParticleSystem,
  createSparkles,
  updateSparkles,
  createConnectionLines,
  updateConnectionLines,
  disposeParticleSystem,
  disposeSparkles,
  disposeConnectionLines,
} from './particles';
import {
  createPawPrint,
  createBone,
  createHeart,
  createMedicalCross,
  createDogSilhouette,
  createCatSilhouette,
  createShelter,
  createStethoscope,
  createMedicine,
  createBall,
  createFish,
  createStar,
} from './shapes';

const rand = (min, max) => Math.random() * (max - min) + min;

const shapeIconFactories = {
  paw: createPawPrint,
  heart: createHeart,
  cross: createMedicalCross,
  shelter: createShelter,
  stethoscope: createStethoscope,
  medicine: createMedicine,
  ball: createBall,
  fish: createFish,
  bone: createBone,
  dog: createDogSilhouette,
  cat: createCatSilhouette,
  star: createStar,
};

const svgIconPaths = {
  bone: '/bone-svgrepo-com.svg',
  dog: '/dog-svgrepo-com.svg',
  cat: '/cat-5-svgrepo-com.svg',
  health: '/health-svgrepo-com.svg',
  star: '/star-alt-4-svgrepo-com.svg',
  bunny: '/bunny-svgrepo-com.svg',
};

const iconPool = [...Object.keys(shapeIconFactories), ...Object.keys(svgIconPaths)];

const svgTextureLoader = new THREE.TextureLoader();

const loadSvgTexture = (path) =>
  new Promise((resolve, reject) => {
    svgTextureLoader.load(
      path,
      (texture) => {
        texture.colorSpace = THREE.SRGBColorSpace;
        texture.needsUpdate = true;
        resolve(texture);
      },
      undefined,
      reject
    );
  });

const createSvgBillboard = (texture, color, scale, opacity) => {
  const material = new THREE.MeshBasicMaterial({
    map: texture,
    color,
    transparent: true,
    opacity,
    depthWrite: false,
    side: THREE.DoubleSide,
    alphaTest: 0.05,
  });

  const plane = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), material);
  plane.scale.setScalar(scale * 0.9);
  return plane;
};

export default function Background3D() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(FOG.COLOR, FOG.DENSITY);

    const width = window.innerWidth;
    const height = window.innerHeight;

    const camera = new THREE.PerspectiveCamera(
      CAMERA.FOV,
      width / height,
      CAMERA.NEAR,
      CAMERA.FAR
    );
    camera.position.set(0, 0, CAMERA.Z);

    const renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: true,
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(0, 8, 10);
    scene.add(ambientLight, directionalLight);

    const particleSystem = createParticleSystem(scene);
    const sparkles = createSparkles(scene);
    const connectionLines = createConnectionLines();
    scene.add(connectionLines);

    const lightRays = new THREE.Group();
    const lightRayMaterials = [];

    for (let i = 0; i < LIGHT_RAYS.COUNT; i += 1) {
      const widthScale = rand(LIGHT_RAYS.WIDTH_MIN, LIGHT_RAYS.WIDTH_MAX);
      const heightScale = rand(LIGHT_RAYS.HEIGHT_MIN, LIGHT_RAYS.HEIGHT_MAX);
      const material = new THREE.MeshBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: LIGHT_RAYS.OPACITY,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        side: THREE.DoubleSide,
      });
      lightRayMaterials.push(material);

      const plane = new THREE.Mesh(
        new THREE.PlaneGeometry(widthScale, heightScale),
        material
      );
      plane.rotation.z = rand(0, Math.PI);
      plane.position.set(
        rand(-WORLD.WIDTH / 2, WORLD.WIDTH / 2),
        rand(-WORLD.HEIGHT / 2, WORLD.HEIGHT / 2),
        -2
      );
      lightRays.add(plane);
    }

    scene.add(lightRays);

    const colors = [
      THREE_COLORS.teal,
      THREE_COLORS.coral,
      THREE_COLORS.lightTeal,
      THREE_COLORS.lightCoral,
      THREE_COLORS.soft,
    ];

    const icons = [];
    const svgTextures = {};

    const loadIconTextures = async () => {
      const entries = Object.entries(svgIconPaths);

      await Promise.all(
        entries.map(async ([type, path]) => {
          svgTextures[type] = await loadSvgTexture(path);
        })
      );

      for (let i = 0; i < ICONS.COUNT; i += 1) {
        const type = iconPool[Math.floor(Math.random() * iconPool.length)];
        const color = colors[Math.floor(Math.random() * colors.length)];
        const scale = rand(ICONS.MIN_SCALE, ICONS.MAX_SCALE);
        const opacity = rand(ICONS.MIN_OPACITY, ICONS.MAX_OPACITY);

        let icon;

        if (svgIconPaths[type]) {
          icon = createSvgBillboard(svgTextures[type], color, scale, opacity);
        } else {
          const iconFactory = shapeIconFactories[type];
          icon = iconFactory(color, scale, opacity);
        }

        icon.position.set(
          rand(-WORLD.WIDTH / 2 + 1.5, WORLD.WIDTH / 2 - 1.5),
          rand(-WORLD.HEIGHT / 2 + 1.2, WORLD.HEIGHT / 2 - 1.2),
          rand(-WORLD.DEPTH / 2 + 1.2, WORLD.DEPTH / 2 - 1.2)
        );

        icon.userData = {
          type,
          baseX: icon.position.x,
          baseY: icon.position.y,
          baseZ: icon.position.z,
          driftSpeed: rand(0.4, 1.2),
          driftAmplitude: rand(0.15, 0.45),
          orbitSpeed: rand(0.08, 0.22),
          orbitRadius: rand(0.08, 0.22),
          phase: rand(0, Math.PI * 2),
          rotationX: rand(-0.004, 0.004),
          rotationY: rand(-0.004, 0.004),
          spinBoost: rand(0.6, 1.4),
          scale,
        };

        scene.add(icon);
        icons.push(icon);
      }
    };

    loadIconTextures();

    const mouse = { x: 0, y: 0, tx: 0, ty: 0, active: false };
    const onMouseMove = (event) => {
      mouse.tx = (event.clientX / window.innerWidth - 0.5) * 1.2;
      mouse.ty = (event.clientY / window.innerHeight - 0.5) * 0.9;
      mouse.active = true;
    };
    const onMouseLeave = () => {
      mouse.active = false;
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseleave', onMouseLeave);

    let rafId;
    const clock = new THREE.Clock();

    const tick = () => {
      rafId = requestAnimationFrame(tick);
      const delta = clock.getDelta();
      const elapsed = clock.getElapsedTime();

      mouse.x += (mouse.tx - mouse.x) * MOUSE.SMOOTHING;
      mouse.y += (mouse.ty - mouse.y) * MOUSE.SMOOTHING;

      camera.position.x = mouse.x * MOUSE.CAMERA_X_STRENGTH;
      camera.position.y = -mouse.y * MOUSE.CAMERA_Y_STRENGTH;
      camera.lookAt(0, 0, 0);

      updateParticleSystem(particleSystem, delta);
      updateSparkles(sparkles, elapsed);
      updateConnectionLines(connectionLines, particleSystem.near);

      lightRays.rotation.z = elapsed * 0.015;
      lightRays.children.forEach((ray, index) => {
        ray.material.opacity =
          LIGHT_RAYS.OPACITY * (0.75 + Math.sin(elapsed * 0.4 + index) * 0.25);
        ray.rotation.z = elapsed * (0.008 + index * 0.0015) + index * 0.7;
      });

      icons.forEach((icon) => {
        const data = icon.userData;
        const orbitX = Math.sin(elapsed * data.orbitSpeed + data.phase) * data.orbitRadius;
        const orbitY = Math.cos(elapsed * data.orbitSpeed * 0.7 + data.phase) * data.orbitRadius * 0.6;
        const driftX = Math.sin(elapsed * data.driftSpeed + data.phase) * data.driftAmplitude;
        const driftY = Math.cos(elapsed * data.driftSpeed * 0.8 + data.phase * 1.2) * data.driftAmplitude * 0.7;

        let repelX = 0;
        let repelY = 0;

        if (mouse.active) {
          const mx = mouse.x * 6;
          const my = -mouse.y * 4.5;
          const dx = data.baseX - mx;
          const dy = data.baseY - my;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < MOUSE.REPULSION_RADIUS) {
            const force =
              ((1 - distance / MOUSE.REPULSION_RADIUS) * MOUSE.REPULSION_STRENGTH) * 6;
            repelX = (dx / (distance || 1)) * force;
            repelY = (dy / (distance || 1)) * force;
          }
        }

        const pulse =
          data.type === 'heart'
            ? 1 + Math.sin(elapsed * ANIMATION.HEART_PULSE_SPEED + data.phase) * ANIMATION.HEART_PULSE_AMOUNT
            : 1;

        icon.position.set(
          data.baseX + driftX + orbitX + repelX,
          data.baseY + driftY + orbitY + repelY,
          data.baseZ + Math.sin(elapsed * 0.4 + data.phase) * 0.15
        );

        icon.rotation.x += data.rotationX;
        icon.rotation.y += data.rotationY;

        if (data.type === 'bone') {
          icon.rotation.z += ANIMATION.BONE_ROTATION_SPEED * data.spinBoost;
        }

        if (data.type === 'heart') {
          icon.scale.setScalar(data.scale * pulse);
        } else {
          icon.scale.setScalar(data.scale);
        }
      });

      renderer.render(scene, camera);
    };

    tick();

    const onResize = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', onResize);

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseleave', onMouseLeave);
      window.removeEventListener('resize', onResize);
      disposeParticleSystem(particleSystem);
      disposeSparkles(sparkles);
      disposeConnectionLines(connectionLines);
      lightRayMaterials.forEach((material) => material.dispose());
      renderer.dispose();
    };
  }, []);

  return (
    <div className="bg3d-scene">
      <canvas ref={canvasRef} className="bg3d-canvas" />
    </div>
  );
}
