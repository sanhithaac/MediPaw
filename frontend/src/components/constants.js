// constants.js

import * as THREE from "three";

/* =========================================
   COLORS
========================================= */

export const COLORS = {
  TEAL: "#1a8a7a",
  LIGHT_TEAL: "#22b8a0",

  CORAL: "#e8756a",
  LIGHT_CORAL: "#f0908a",

  SOFT_BLUE: "#c4d6e0",
  WHITE: "#ffffff",

  BACKGROUND_TOP: "#eaf8f5",
  BACKGROUND_BOTTOM: "#fff4f2",
};

/* =========================================
   CAMERA
========================================= */

export const CAMERA = {
  FOV: 70,
  NEAR: 0.1,
  FAR: 100,
  Z: 6,
};

/* =========================================
   PARTICLES
========================================= */

export const PARTICLES = {
  NEAR_COUNT: 350,
  MID_COUNT: 500,
  FAR_COUNT: 750,

  NEAR_SIZE: 0.06,
  MID_SIZE: 0.04,
  FAR_SIZE: 0.025,

  NEAR_OPACITY: 0.45,
  MID_OPACITY: 0.30,
  FAR_OPACITY: 0.18,
};

/* =========================================
   CONNECTING LINES
========================================= */

export const CONNECTIONS = {
  MAX_DISTANCE: 1.8,
  OPACITY: 0.08,
};

/* =========================================
   FLOATING ICONS
========================================= */

export const ICONS = {
  COUNT: 40,

  MIN_SCALE: 0.5,
  MAX_SCALE: 2.0,

  MIN_OPACITY: 0.05,
  MAX_OPACITY: 0.16,

  FLOAT_SPEED_MIN: 0.15,
  FLOAT_SPEED_MAX: 0.6,

  ORBIT_SPEED_MIN: 0.05,
  ORBIT_SPEED_MAX: 0.25,

  ORBIT_RADIUS_MIN: 0.1,
  ORBIT_RADIUS_MAX: 0.8,
};

/* =========================================
   SPARKLES
========================================= */

export const SPARKLES = {
  COUNT: 120,
  SIZE: 0.03,
  OPACITY: 0.6,
};

/* =========================================
   LIGHT RAYS
========================================= */

export const LIGHT_RAYS = {
  COUNT: 8,

  WIDTH_MIN: 2,
  WIDTH_MAX: 5,

  HEIGHT_MIN: 8,
  HEIGHT_MAX: 14,

  OPACITY: 0.03,
};

/* =========================================
   MOUSE PARALLAX
========================================= */

export const MOUSE = {
  CAMERA_X_STRENGTH: 0.5,
  CAMERA_Y_STRENGTH: 0.35,

  SMOOTHING: 0.04,

  REPULSION_RADIUS: 1.5,
  REPULSION_STRENGTH: 0.03,
};

/* =========================================
   FOG
========================================= */

export const FOG = {
  COLOR: 0xffffff,
  DENSITY: 0.03,
};

/* =========================================
   ANIMATION
========================================= */

export const ANIMATION = {
  PARTICLE_ROTATION_X: 0.005,
  PARTICLE_ROTATION_Y: 0.012,

  HEART_PULSE_SPEED: 2.0,
  HEART_PULSE_AMOUNT: 0.08,

  BONE_ROTATION_SPEED: 0.003,

  ICON_DRIFT_AMOUNT: 0.35,
};

/* =========================================
   WORLD BOUNDS
========================================= */

export const WORLD = {
  WIDTH: 24,
  HEIGHT: 18,
  DEPTH: 12,
};

/* =========================================
   PREBUILT THREE COLORS
========================================= */

export const THREE_COLORS = {
  teal: new THREE.Color(COLORS.TEAL),
  coral: new THREE.Color(COLORS.CORAL),
  soft: new THREE.Color(COLORS.SOFT_BLUE),

  lightTeal: new THREE.Color(COLORS.LIGHT_TEAL),
  lightCoral: new THREE.Color(COLORS.LIGHT_CORAL),
};
