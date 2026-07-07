// particles.js

import * as THREE from "three";
import {
  PARTICLES,
  WORLD,
  THREE_COLORS,
  CONNECTIONS,
  SPARKLES,
} from "./constants";

/* ==========================================================
   RANDOM HELPERS
========================================================== */

const rand = (min, max) => Math.random() * (max - min) + min;

const randomColor = () => {
  const r = Math.random();

  if (r < 0.35) return THREE_COLORS.teal;
  if (r < 0.55) return THREE_COLORS.coral;
  if (r < 0.75) return THREE_COLORS.lightTeal;
  if (r < 0.9) return THREE_COLORS.lightCoral;

  return THREE_COLORS.soft;
};

/* ==========================================================
   PARTICLE LAYER
========================================================== */

export function createParticleLayer({
  count,
  size,
  opacity,
  spread = WORLD,
}) {
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);

  const velocity = [];

  for (let i = 0; i < count; i++) {
    positions[i * 3] = rand(-spread.WIDTH / 2, spread.WIDTH / 2);

    positions[i * 3 + 1] = rand(
      -spread.HEIGHT / 2,
      spread.HEIGHT / 2
    );

    positions[i * 3 + 2] = rand(
      -spread.DEPTH / 2,
      spread.DEPTH / 2
    );

    const c = randomColor();

    colors[i * 3] = c.r;
    colors[i * 3 + 1] = c.g;
    colors[i * 3 + 2] = c.b;

    velocity.push({
      x: rand(-0.002, 0.002),
      y: rand(-0.002, 0.002),
      z: rand(-0.001, 0.001),
    });
  }

  const geometry = new THREE.BufferGeometry();

  geometry.setAttribute(
    "position",
    new THREE.BufferAttribute(positions, 3)
  );

  geometry.setAttribute(
    "color",
    new THREE.BufferAttribute(colors, 3)
  );

  const material = new THREE.PointsMaterial({
    size,
    vertexColors: true,
    transparent: true,
    opacity,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    sizeAttenuation: true,
  });

  const points = new THREE.Points(geometry, material);

  points.userData.velocity = velocity;

  return points;
}

/* ==========================================================
   CREATE ALL THREE LAYERS
========================================================== */

export function createParticleSystem(scene) {
  const near = createParticleLayer({
    count: PARTICLES.NEAR_COUNT,
    size: PARTICLES.NEAR_SIZE,
    opacity: PARTICLES.NEAR_OPACITY,
  });

  const mid = createParticleLayer({
    count: PARTICLES.MID_COUNT,
    size: PARTICLES.MID_SIZE,
    opacity: PARTICLES.MID_OPACITY,
  });

  const far = createParticleLayer({
    count: PARTICLES.FAR_COUNT,
    size: PARTICLES.FAR_SIZE,
    opacity: PARTICLES.FAR_OPACITY,
  });

  scene.add(far);
  scene.add(mid);
  scene.add(near);

  return {
    near,
    mid,
    far,
  };
}

/* ==========================================================
   SPARKLES
========================================================== */

export function createSparkles(scene) {
  const count = SPARKLES.COUNT;

  const geometry = new THREE.BufferGeometry();

  const positions = new Float32Array(count * 3);

  for (let i = 0; i < count; i++) {
    positions[i * 3] = rand(-WORLD.WIDTH / 2, WORLD.WIDTH / 2);

    positions[i * 3 + 1] = rand(
      -WORLD.HEIGHT / 2,
      WORLD.HEIGHT / 2
    );

    positions[i * 3 + 2] = rand(
      -WORLD.DEPTH / 2,
      WORLD.DEPTH / 2
    );
  }

  geometry.setAttribute(
    "position",
    new THREE.BufferAttribute(positions, 3)
  );

  const material = new THREE.PointsMaterial({
    color: 0xffffff,
    transparent: true,
    opacity: SPARKLES.OPACITY,
    size: SPARKLES.SIZE,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });

  const sparkles = new THREE.Points(
    geometry,
    material
  );

  sparkles.userData.twinkle = [];

  for (let i = 0; i < count; i++) {
    sparkles.userData.twinkle.push({
      phase: Math.random() * Math.PI * 2,
      speed: rand(0.5, 2),
    });
  }

  scene.add(sparkles);

  return sparkles;
}

/* ==========================================================
   CONNECTION LINES
========================================================== */

export function createConnectionLines() {
  const geometry = new THREE.BufferGeometry();

  const material = new THREE.LineBasicMaterial({
    color: 0xffffff,
    transparent: true,
    opacity: CONNECTIONS.OPACITY,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });

  const lines = new THREE.LineSegments(
    geometry,
    material
  );

  return lines;
}

/* ==========================================================
   UPDATE SINGLE PARTICLE LAYER
========================================================== */

export function updateParticleLayer(points, delta = 1) {
  const positions = points.geometry.attributes.position.array;
  const velocity = points.userData.velocity;

  for (let i = 0; i < velocity.length; i++) {
    const v = velocity[i];

    const x = i * 3;
    const y = x + 1;
    const z = x + 2;

    positions[x] += v.x * delta;
    positions[y] += v.y * delta;
    positions[z] += v.z * delta;

    if (positions[x] > WORLD.WIDTH / 2) positions[x] = -WORLD.WIDTH / 2;
    if (positions[x] < -WORLD.WIDTH / 2) positions[x] = WORLD.WIDTH / 2;

    if (positions[y] > WORLD.HEIGHT / 2) positions[y] = -WORLD.HEIGHT / 2;
    if (positions[y] < -WORLD.HEIGHT / 2) positions[y] = WORLD.HEIGHT / 2;

    if (positions[z] > WORLD.DEPTH / 2) positions[z] = -WORLD.DEPTH / 2;
    if (positions[z] < -WORLD.DEPTH / 2) positions[z] = WORLD.DEPTH / 2;
  }

  points.geometry.attributes.position.needsUpdate = true;
}

/* ==========================================================
   UPDATE ALL PARTICLE LAYERS
========================================================== */

export function updateParticleSystem(system, delta) {
  updateParticleLayer(system.near, delta);
  updateParticleLayer(system.mid, delta);
  updateParticleLayer(system.far, delta);

  system.near.rotation.y += 0.0004;
  system.mid.rotation.y += 0.00025;
  system.far.rotation.y += 0.0001;

  system.near.rotation.x += 0.00015;
  system.mid.rotation.x += 0.00008;
  system.far.rotation.x += 0.00004;
}

/* ==========================================================
   UPDATE SPARKLES
========================================================== */

export function updateSparkles(sparkles, elapsedTime) {
  const material = sparkles.material;

  let alpha = 0;

  sparkles.userData.twinkle.forEach((s) => {
    alpha += (Math.sin(elapsedTime * s.speed + s.phase) + 1) * 0.5;
  });

  alpha /= sparkles.userData.twinkle.length;

  material.opacity =
    SPARKLES.OPACITY * (0.4 + alpha * 0.6);

  sparkles.rotation.y += 0.0008;
  sparkles.rotation.x += 0.00025;
}

/* ==========================================================
   UPDATE CONNECTION LINES
========================================================== */

export function updateConnectionLines(lines, particleLayer) {
  const pos =
    particleLayer.geometry.attributes.position.array;

  const vertices = [];

  const maxDistanceSq =
    CONNECTIONS.MAX_DISTANCE *
    CONNECTIONS.MAX_DISTANCE;

  const particleCount = pos.length / 3;

  for (let i = 0; i < particleCount; i++) {
    const ix = i * 3;

    for (let j = i + 1; j < particleCount; j++) {
      const jx = j * 3;

      const dx = pos[ix] - pos[jx];
      const dy = pos[ix + 1] - pos[jx + 1];
      const dz = pos[ix + 2] - pos[jx + 2];

      const distSq =
        dx * dx +
        dy * dy +
        dz * dz;

      if (distSq < maxDistanceSq) {
        vertices.push(
          pos[ix],
          pos[ix + 1],
          pos[ix + 2]
        );

        vertices.push(
          pos[jx],
          pos[jx + 1],
          pos[jx + 2]
        );
      }
    }
  }

  lines.geometry.dispose();

  lines.geometry = new THREE.BufferGeometry();

  lines.geometry.setAttribute(
    "position",
    new THREE.Float32BufferAttribute(vertices, 3)
  );
}

/* ==========================================================
   DISPOSE
========================================================== */

export function disposeParticleSystem(system) {
  [system.near, system.mid, system.far].forEach((layer) => {
    layer.geometry.dispose();
    layer.material.dispose();
  });
}

export function disposeSparkles(sparkles) {
  sparkles.geometry.dispose();
  sparkles.material.dispose();
}

export function disposeConnectionLines(lines) {
  lines.geometry.dispose();
  lines.material.dispose();
}
