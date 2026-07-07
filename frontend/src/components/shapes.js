// shapes.js

import * as THREE from "three";

/* ==========================================================
   Helper Material
========================================================== */

function createMaterial(color, opacity = 0.12) {
  return new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
}

/* ==========================================================
   Paw Print
========================================================== */

export function createPawPrint(color, scale = 1, opacity = 0.12) {
  const group = new THREE.Group();
  const material = createMaterial(color, opacity);

  const main = new THREE.Shape();
  main.absellipse(0, 0, 0.28 * scale, 0.22 * scale, 0, Math.PI * 2);

  group.add(new THREE.Mesh(new THREE.ShapeGeometry(main, 24), material));

  const toes = [
    [-0.16, 0.24],
    [0.16, 0.24],
    [-0.27, 0.08],
    [0.27, 0.08],
  ];

  toes.forEach(([x, y]) => {
    const toe = new THREE.Shape();
    toe.absellipse(
      0,
      0,
      0.09 * scale,
      0.11 * scale,
      0,
      Math.PI * 2
    );

    const mesh = new THREE.Mesh(
      new THREE.ShapeGeometry(toe, 20),
      material
    );

    mesh.position.set(x * scale, y * scale, 0);

    group.add(mesh);
  });

  return group;
}

/* ==========================================================
   Bone
========================================================== */

export function createBone(color, scale = 1, opacity = 0.1) {
  const group = new THREE.Group();
  const material = createMaterial(color, opacity);

  const shaft = new THREE.Shape();

  shaft.moveTo(-0.35 * scale, -0.05 * scale);
  shaft.lineTo(0.35 * scale, -0.05 * scale);
  shaft.lineTo(0.35 * scale, 0.05 * scale);
  shaft.lineTo(-0.35 * scale, 0.05 * scale);
  shaft.closePath();

  group.add(new THREE.Mesh(new THREE.ShapeGeometry(shaft), material));

  const circles = [
    [-0.35, 0.08],
    [-0.35, -0.08],
    [0.35, 0.08],
    [0.35, -0.08],
  ];

  circles.forEach(([x, y]) => {
    const shape = new THREE.Shape();

    shape.absellipse(
      0,
      0,
      0.09 * scale,
      0.09 * scale,
      0,
      Math.PI * 2
    );

    const mesh = new THREE.Mesh(
      new THREE.ShapeGeometry(shape, 20),
      material
    );

    mesh.position.set(x * scale, y * scale, 0);

    group.add(mesh);
  });

  return group;
}

/* ==========================================================
   Heart
========================================================== */

export function createHeart(color, scale = 1, opacity = 0.1) {
  const material = createMaterial(color, opacity);

  const s = 0.3 * scale;

  const shape = new THREE.Shape();

  shape.moveTo(0, s * 0.25);

  shape.bezierCurveTo(
    0,
    s * 0.65,
    -s * 0.7,
    s * 0.8,
    -s * 0.7,
    s * 0.3
  );

  shape.bezierCurveTo(
    -s * 0.7,
    -s * 0.2,
    0,
    -s * 0.35,
    0,
    -s * 0.65
  );

  shape.bezierCurveTo(
    0,
    -s * 0.35,
    s * 0.7,
    -s * 0.2,
    s * 0.7,
    s * 0.3
  );

  shape.bezierCurveTo(
    s * 0.7,
    s * 0.8,
    0,
    s * 0.65,
    0,
    s * 0.25
  );

  return new THREE.Mesh(new THREE.ShapeGeometry(shape, 24), material);
}

/* ==========================================================
   Medical Cross
========================================================== */

export function createMedicalCross(color, scale = 1, opacity = 0.1) {
  const material = createMaterial(color, opacity);

  const s = 0.25 * scale;
  const t = s * 0.35;

  const shape = new THREE.Shape();

  shape.moveTo(-t, s);
  shape.lineTo(t, s);
  shape.lineTo(t, t);

  shape.lineTo(s, t);
  shape.lineTo(s, -t);

  shape.lineTo(t, -t);
  shape.lineTo(t, -s);

  shape.lineTo(-t, -s);
  shape.lineTo(-t, -t);

  shape.lineTo(-s, -t);
  shape.lineTo(-s, t);

  shape.lineTo(-t, t);

  shape.closePath();

  return new THREE.Mesh(new THREE.ShapeGeometry(shape), material);
}

/* ==========================================================
   Dog Silhouette
========================================================== */

export function createDogSilhouette(color, scale = 1, opacity = 0.1) {
  const group = new THREE.Group();
  const material = createMaterial(color, opacity);

  const body = new THREE.Shape();
  body.absellipse(0, 0, 0.16 * scale, 0.13 * scale, 0, Math.PI * 2);
  group.add(new THREE.Mesh(new THREE.ShapeGeometry(body, 24), material));

  const head = new THREE.Shape();
  head.absellipse(0, 0, 0.12 * scale, 0.1 * scale, 0, Math.PI * 2);
  const headMesh = new THREE.Mesh(new THREE.ShapeGeometry(head, 20), material);
  headMesh.position.set(0.18 * scale, 0.1 * scale, 0);
  group.add(headMesh);

  const ear = new THREE.Shape();
  ear.moveTo(-0.03 * scale, 0.03 * scale);
  ear.lineTo(0.02 * scale, 0.14 * scale);
  ear.lineTo(0.06 * scale, 0.03 * scale);
  ear.closePath();

  const leftEar = new THREE.Mesh(new THREE.ShapeGeometry(ear), material);
  leftEar.position.set(0.15 * scale, 0.16 * scale, 0);
  group.add(leftEar);

  const rightEar = new THREE.Mesh(new THREE.ShapeGeometry(ear), material);
  rightEar.position.set(0.22 * scale, 0.16 * scale, 0);
  group.add(rightEar);

  return group;
}

/* ==========================================================
   Cat Silhouette
========================================================== */

export function createCatSilhouette(color, scale = 1, opacity = 0.1) {
  const group = new THREE.Group();
  const material = createMaterial(color, opacity);

  const body = new THREE.Shape();
  body.absellipse(0, 0, 0.16 * scale, 0.12 * scale, 0, Math.PI * 2);
  group.add(new THREE.Mesh(new THREE.ShapeGeometry(body, 24), material));

  const head = new THREE.Shape();
  head.absellipse(0, 0, 0.11 * scale, 0.09 * scale, 0, Math.PI * 2);
  const headMesh = new THREE.Mesh(new THREE.ShapeGeometry(head, 20), material);
  headMesh.position.set(0.18 * scale, 0.11 * scale, 0);
  group.add(headMesh);

  const ear = new THREE.Shape();
  ear.moveTo(-0.03 * scale, 0.04 * scale);
  ear.lineTo(0.01 * scale, 0.13 * scale);
  ear.lineTo(0.05 * scale, 0.03 * scale);
  ear.closePath();

  const leftEar = new THREE.Mesh(new THREE.ShapeGeometry(ear), material);
  leftEar.position.set(0.14 * scale, 0.18 * scale, 0);
  group.add(leftEar);

  const rightEar = new THREE.Mesh(new THREE.ShapeGeometry(ear), material);
  rightEar.position.set(0.22 * scale, 0.18 * scale, 0);
  group.add(rightEar);

  return group;
}

/* ==========================================================
   Shelter
========================================================== */

export function createShelter(color, scale = 1, opacity = 0.1) {
  const group = new THREE.Group();
  const material = createMaterial(color, opacity);

  const body = new THREE.Shape();
  body.moveTo(-0.2 * scale, -0.1 * scale);
  body.lineTo(0.2 * scale, -0.1 * scale);
  body.lineTo(0.2 * scale, 0.1 * scale);
  body.lineTo(-0.2 * scale, 0.1 * scale);
  body.closePath();
  group.add(new THREE.Mesh(new THREE.ShapeGeometry(body), material));

  const roof = new THREE.Shape();
  roof.moveTo(-0.24 * scale, 0.1 * scale);
  roof.lineTo(0 * scale, 0.24 * scale);
  roof.lineTo(0.24 * scale, 0.1 * scale);
  roof.closePath();
  const roofMesh = new THREE.Mesh(new THREE.ShapeGeometry(roof), material);
  roofMesh.position.set(0, 0.01 * scale, 0);
  group.add(roofMesh);

  const door = new THREE.Shape();
  door.absellipse(0, 0, 0.04 * scale, 0.06 * scale, 0, Math.PI * 2);
  const doorMesh = new THREE.Mesh(new THREE.ShapeGeometry(door), material);
  doorMesh.position.set(0, -0.03 * scale, 0);
  group.add(doorMesh);

  return group;
}

/* ==========================================================
   Stethoscope
========================================================== */

export function createStethoscope(color, scale = 1, opacity = 0.1) {
  const group = new THREE.Group();
  const material = createMaterial(color, opacity);

  const tube = new THREE.Mesh(
    new THREE.CylinderGeometry(0.02 * scale, 0.02 * scale, 0.28 * scale, 10),
    material
  );
  tube.rotation.z = 0.35;
  tube.position.set(-0.04 * scale, 0.03 * scale, 0);
  group.add(tube);

  const chest = new THREE.Mesh(
    new THREE.CircleGeometry(0.06 * scale, 16),
    material
  );
  chest.position.set(-0.16 * scale, -0.1 * scale, 0);
  group.add(chest);

  return group;
}

/* ==========================================================
   Medicine
========================================================== */

export function createMedicine(color, scale = 1, opacity = 0.1) {
  const group = new THREE.Group();
  const material = createMaterial(color, opacity);

  const body = new THREE.Shape();
  body.moveTo(-0.13 * scale, -0.08 * scale);
  body.lineTo(0.13 * scale, -0.08 * scale);
  body.lineTo(0.13 * scale, 0.08 * scale);
  body.lineTo(-0.13 * scale, 0.08 * scale);
  body.closePath();
  group.add(new THREE.Mesh(new THREE.ShapeGeometry(body), material));

  const stripe = new THREE.Shape();
  stripe.moveTo(-0.03 * scale, -0.11 * scale);
  stripe.lineTo(0.03 * scale, -0.11 * scale);
  stripe.lineTo(0.03 * scale, 0.11 * scale);
  stripe.lineTo(-0.03 * scale, 0.11 * scale);
  stripe.closePath();
  const stripeMesh = new THREE.Mesh(new THREE.ShapeGeometry(stripe), material);
  stripeMesh.position.set(0, 0, 0);
  group.add(stripeMesh);

  return group;
}

/* ==========================================================
   Ball
========================================================== */

export function createBall(color, scale = 1, opacity = 0.1) {
  const group = new THREE.Group();
  const material = createMaterial(color, opacity);

  const sphere = new THREE.Mesh(
    new THREE.CircleGeometry(0.16 * scale, 24),
    material
  );
  group.add(sphere);

  const seam = new THREE.Mesh(
    new THREE.CylinderGeometry(0.01 * scale, 0.01 * scale, 0.24 * scale, 8),
    material
  );
  seam.rotation.z = Math.PI / 2;
  seam.position.set(0, 0, 0);
  group.add(seam);

  return group;
}

/* ==========================================================
   Dog Tag
========================================================== */

export function createDogTag(color, scale = 1, opacity = 0.1) {
  const group = new THREE.Group();
  const material = createMaterial(color, opacity);

  const body = new THREE.Shape();

  body.absellipse(
    0,
    0,
    0.22 * scale,
    0.32 * scale,
    0,
    Math.PI * 2
  );

  group.add(new THREE.Mesh(new THREE.ShapeGeometry(body, 32), material));

  const hole = new THREE.Shape();

  hole.absellipse(
    0,
    0,
    0.035 * scale,
    0.035 * scale,
    0,
    Math.PI * 2
  );

  const holeMesh = new THREE.Mesh(
    new THREE.ShapeGeometry(hole, 16),
    new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.25,
      depthWrite: false,
    })
  );

  holeMesh.position.y = 0.18 * scale;

  group.add(holeMesh);

  return group;
}

/* ==========================================================
   Fish
========================================================== */

export function createFish(color, scale = 1, opacity = 0.1) {
  const material = createMaterial(color, opacity);

  const shape = new THREE.Shape();

  shape.moveTo(-0.25 * scale, 0);

  shape.quadraticCurveTo(
    0,
    0.22 * scale,
    0.28 * scale,
    0
  );

  shape.quadraticCurveTo(
    0,
    -0.22 * scale,
    -0.25 * scale,
    0
  );

  shape.lineTo(-0.42 * scale, 0.18 * scale);

  shape.lineTo(-0.34 * scale, 0);

  shape.lineTo(-0.42 * scale, -0.18 * scale);

  shape.closePath();

  return new THREE.Mesh(new THREE.ShapeGeometry(shape, 24), material);
}

/* ==========================================================
   Star
========================================================== */

export function createStar(color, scale = 1, opacity = 0.12) {
  const material = createMaterial(color, opacity);

  const shape = new THREE.Shape();

  const outer = 0.28 * scale;
  const inner = outer * 0.45;

  for (let i = 0; i < 10; i++) {
    const angle = (i / 10) * Math.PI * 2 - Math.PI / 2;

    const radius = i % 2 === 0 ? outer : inner;

    const x = Math.cos(angle) * radius;
    const y = Math.sin(angle) * radius;

    if (i === 0)
      shape.moveTo(x, y);
    else
      shape.lineTo(x, y);
  }

  shape.closePath();

  return new THREE.Mesh(new THREE.ShapeGeometry(shape), material);
}
