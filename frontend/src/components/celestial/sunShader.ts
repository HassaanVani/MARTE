/**
 * Procedural Sun shaders — animated turbulent plasma surface.
 * Produces a realistic-looking star without texture dependencies.
 */

export const sunVertexShader = /* glsl */ `
  varying vec3 vNormal;
  varying vec3 vPosition;
  varying vec2 vUv;

  void main() {
    vNormal = normalize(normalMatrix * normal);
    vPosition = position;
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

export const sunFragmentShader = /* glsl */ `
  uniform float uTime;

  varying vec3 vNormal;
  varying vec3 vPosition;
  varying vec2 vUv;

  // Simplex-style noise — fast 3D hash-based
  vec3 hash33(vec3 p) {
    p = fract(p * vec3(443.8975, 397.2973, 491.1871));
    p += dot(p, p.yxz + 19.19);
    return fract((p.xxy + p.yxx) * p.zyx);
  }

  float noise3d(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);

    float n = mix(
      mix(
        mix(dot(hash33(i), f), dot(hash33(i + vec3(1,0,0)), f - vec3(1,0,0)), f.x),
        mix(dot(hash33(i + vec3(0,1,0)), f - vec3(0,1,0)), dot(hash33(i + vec3(1,1,0)), f - vec3(1,1,0)), f.x),
        f.y
      ),
      mix(
        mix(dot(hash33(i + vec3(0,0,1)), f - vec3(0,0,1)), dot(hash33(i + vec3(1,0,1)), f - vec3(1,0,1)), f.x),
        mix(dot(hash33(i + vec3(0,1,1)), f - vec3(0,1,1)), dot(hash33(i + vec3(1,1,1)), f - vec3(1,1,1)), f.x),
        f.y
      ),
      f.z
    );
    return n * 0.5 + 0.5;
  }

  // Fractal Brownian Motion for turbulence
  float fbm(vec3 p) {
    float value = 0.0;
    float amplitude = 0.5;
    float frequency = 1.0;
    for (int i = 0; i < 5; i++) {
      value += amplitude * noise3d(p * frequency);
      amplitude *= 0.5;
      frequency *= 2.0;
    }
    return value;
  }

  void main() {
    // Animated 3D position for turbulence sampling
    vec3 samplePos = vPosition * 3.0 + vec3(uTime * 0.05, uTime * 0.03, uTime * 0.04);

    // Two layers of turbulence for convection cells
    float turb1 = fbm(samplePos);
    float turb2 = fbm(samplePos * 2.0 + vec3(100.0));

    // Combine turbulence layers
    float turb = turb1 * 0.7 + turb2 * 0.3;

    // Solar surface colors — from dark orange granules to bright yellow/white
    vec3 darkGranule = vec3(0.85, 0.35, 0.05);  // dark orange
    vec3 midSurface  = vec3(1.0, 0.65, 0.15);   // bright orange
    vec3 hotSpot     = vec3(1.0, 0.92, 0.6);     // yellow-white

    vec3 color;
    if (turb < 0.45) {
      color = mix(darkGranule, midSurface, turb / 0.45);
    } else if (turb < 0.7) {
      color = mix(midSurface, hotSpot, (turb - 0.45) / 0.25);
    } else {
      color = hotSpot;
    }

    // Limb darkening — edges of the sun are darker/redder
    float NdotV = max(dot(vNormal, vec3(0.0, 0.0, 1.0)), 0.0);
    float limb = pow(NdotV, 0.4);
    color *= mix(0.4, 1.0, limb);

    // Slight reddening at limb
    color.r += (1.0 - limb) * 0.15;
    color.g *= mix(0.7, 1.0, limb);

    gl_FragColor = vec4(color, 1.0);
  }
`;

export const sunCoronaVertexShader = /* glsl */ `
  varying vec3 vNormal;
  varying vec3 vWorldPos;

  void main() {
    vNormal = normalize(normalMatrix * normal);
    vWorldPos = (modelMatrix * vec4(position, 1.0)).xyz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

export const sunCoronaFragmentShader = /* glsl */ `
  uniform float uTime;

  varying vec3 vNormal;
  varying vec3 vWorldPos;

  void main() {
    // View-facing glow (fresnel-like)
    float NdotV = max(dot(vNormal, normalize(cameraPosition - vWorldPos)), 0.0);
    float glow = pow(1.0 - NdotV, 2.5);

    // Flickering
    float flicker = 0.85 + 0.15 * sin(uTime * 3.0 + vWorldPos.x * 10.0);

    vec3 color = vec3(1.0, 0.6, 0.1) * glow * flicker;
    float alpha = glow * 0.35 * flicker;

    gl_FragColor = vec4(color, alpha);
  }
`;
