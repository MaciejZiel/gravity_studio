import * as THREE from "three";

const vertex = /* glsl */ `
varying vec2 vUv;
varying vec3 vNormalW;
varying vec3 vPosW;
void main() {
  vUv = uv;
  vNormalW = normalize(mat3(modelMatrix) * normal);
  vec4 w = modelMatrix * vec4(position, 1.0);
  vPosW = w.xyz;
  gl_Position = projectionMatrix * viewMatrix * w;
}`;

const fragment = /* glsl */ `
uniform sampler2D dayMap;
uniform sampler2D nightMap;
varying vec2 vUv;
varying vec3 vNormalW;
varying vec3 vPosW;
void main() {
  vec3 n = normalize(vNormalW);
  vec3 sunDir = normalize(-vPosW); // the Sun sits at the scene origin
  float d = dot(n, sunDir);
  float dayMix = smoothstep(-0.12, 0.18, d);
  vec3 day = texture2D(dayMap, vUv).rgb;
  vec3 night = texture2D(nightMap, vUv).rgb;
  vec3 lit = day * (max(d, 0.0) * 1.2 + 0.03);
  vec3 dark = night * vec3(1.0, 0.82, 0.55) * 1.3 + day * 0.02;
  gl_FragColor = vec4(mix(dark, lit, dayMix), 1.0);
  #include <colorspace_fragment>
}`;

export function earthMaterial(day: THREE.Texture, night: THREE.Texture): THREE.ShaderMaterial {
  return new THREE.ShaderMaterial({
    uniforms: { dayMap: { value: day }, nightMap: { value: night } },
    vertexShader: vertex,
    fragmentShader: fragment,
  });
}

const atmoVertex = /* glsl */ `
varying vec3 vNormalV;
varying vec3 vNormalW;
varying vec3 vPosW;
void main() {
  vNormalV = normalize(normalMatrix * normal);
  vNormalW = normalize(mat3(modelMatrix) * normal);
  vec4 w = modelMatrix * vec4(position, 1.0);
  vPosW = w.xyz;
  gl_Position = projectionMatrix * viewMatrix * w;
}`;

const atmoFragment = /* glsl */ `
varying vec3 vNormalV;
varying vec3 vNormalW;
varying vec3 vPosW;
uniform vec3 tint;
void main() {
  float rim = pow(max(0.0, 0.62 - dot(normalize(vNormalV), vec3(0.0, 0.0, 1.0))), 3.0);
  float sun = smoothstep(-0.25, 0.4, dot(normalize(vNormalW), normalize(-vPosW)));
  gl_FragColor = vec4(tint * rim * 2.2 * sun, 1.0);
  #include <colorspace_fragment>
}`;

/** Additive back-face shell that gives Earth a thin blue limb. */
export function atmosphereMaterial(tint: THREE.Color): THREE.ShaderMaterial {
  return new THREE.ShaderMaterial({
    uniforms: { tint: { value: tint } },
    vertexShader: atmoVertex,
    fragmentShader: atmoFragment,
    side: THREE.BackSide,
    blending: THREE.AdditiveBlending,
    transparent: true,
    depthWrite: false,
  });
}
