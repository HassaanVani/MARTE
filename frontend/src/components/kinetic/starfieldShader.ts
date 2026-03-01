export const starfieldVertexShader = /* glsl */ `
  uniform float uBeta;
  uniform float uGamma;
  uniform vec3 uVelocityDir;
  uniform float uTime;

  attribute float aSize;
  attribute vec3 aColor;
  attribute float aBrightness;

  varying vec3 vColor;
  varying float vAlpha;

  void main() {
    vec3 dir = normalize(position);
    float cosTheta = dot(dir, uVelocityDir);

    // Relativistic aberration
    float denom = 1.0 - uBeta * cosTheta;
    float cosThetaPrime = (cosTheta - uBeta) / max(denom, 0.001);
    cosThetaPrime = clamp(cosThetaPrime, -1.0, 1.0);

    // Doppler factor
    float doppler = 1.0 / max(uGamma * denom, 0.01);
    doppler = clamp(doppler, 0.1, 10.0);

    // Relativistic beaming: intensity proportional to D^3
    float beaming = doppler * doppler * doppler;
    beaming = clamp(beaming, 0.005, 80.0);

    // Reconstruct aberrated direction
    float sinTheta = sqrt(1.0 - cosTheta * cosTheta);
    float sinThetaPrime = sqrt(1.0 - cosThetaPrime * cosThetaPrime);

    vec3 aberratedDir;
    if (sinTheta > 0.001) {
      vec3 perpDir = (dir - cosTheta * uVelocityDir) / sinTheta;
      aberratedDir = cosThetaPrime * uVelocityDir + sinThetaPrime * perpDir;
    } else {
      aberratedDir = sign(cosTheta) * uVelocityDir;
    }

    float radius = length(position);
    vec3 aberratedPos = aberratedDir * radius;

    // Doppler color shift — more dramatic
    vec3 baseColor = aColor;
    if (doppler > 1.0) {
      float blueShift = min((doppler - 1.0) * 0.7, 1.0);
      baseColor = mix(baseColor, vec3(0.5, 0.6, 1.0), blueShift);
    } else {
      float redShift = min((1.0 - doppler) * 0.7, 1.0);
      baseColor = mix(baseColor, vec3(1.0, 0.3, 0.1), redShift);
    }

    // Apply beaming to color with high brightness stars getting extra pop
    vColor = baseColor * beaming * (0.5 + aBrightness * 1.5);
    vAlpha = clamp(beaming * aBrightness, 0.08, 1.0);

    vec4 mvPosition = modelViewMatrix * vec4(aberratedPos, 1.0);
    gl_Position = projectionMatrix * mvPosition;

    // Bigger base size, more beaming influence
    float basePtSize = aSize * (400.0 / -mvPosition.z);
    gl_PointSize = basePtSize * (0.5 + beaming * 0.5);
    gl_PointSize = clamp(gl_PointSize, 0.8, 12.0);
  }
`;

export const starfieldFragmentShader = /* glsl */ `
  varying vec3 vColor;
  varying float vAlpha;

  void main() {
    vec2 center = gl_PointCoord - vec2(0.5);
    float dist = length(center);
    if (dist > 0.5) discard;

    // Bright core with soft halo
    float core = smoothstep(0.5, 0.05, dist);
    float halo = smoothstep(0.5, 0.3, dist) * 0.3;
    float brightness = core + halo;

    gl_FragColor = vec4(vColor * brightness, vAlpha * brightness);
  }
`;

// Warp speed lines — stretched along velocity when β is high
export const warpVertexShader = /* glsl */ `
  uniform float uBeta;
  uniform vec3 uVelocityDir;
  uniform float uTime;

  attribute float aOffset;
  attribute float aSpeed;

  varying float vAlpha;
  varying float vStretch;

  void main() {
    // Only visible above β > 0.3
    float visibility = smoothstep(0.3, 0.6, uBeta);
    if (visibility < 0.01) {
      gl_Position = vec4(0.0, 0.0, -10.0, 1.0);
      vAlpha = 0.0;
      vStretch = 0.0;
      return;
    }

    // Each line is a point that streaks past
    float t = fract(aOffset + uTime * aSpeed * (0.5 + uBeta * 2.0));

    // Position along a tube around velocity direction
    float angle = aOffset * 6.28318;
    float radius = 2.0 + aOffset * 18.0;

    // Create perpendicular vectors to velocity
    vec3 up = abs(uVelocityDir.y) < 0.99 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0);
    vec3 right = normalize(cross(uVelocityDir, up));
    vec3 realUp = normalize(cross(right, uVelocityDir));

    vec3 pos = uVelocityDir * (t * 80.0 - 40.0)
             + right * cos(angle) * radius
             + realUp * sin(angle) * radius;

    vAlpha = visibility * (1.0 - abs(t * 2.0 - 1.0)) * 0.6;
    vStretch = uBeta;

    vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
    gl_Position = projectionMatrix * mvPosition;

    // Lines get longer with higher beta
    float streakLength = 2.0 + uBeta * 8.0;
    gl_PointSize = clamp(streakLength * (200.0 / -mvPosition.z), 1.0, streakLength * 3.0);
  }
`;

export const warpFragmentShader = /* glsl */ `
  varying float vAlpha;
  varying float vStretch;

  void main() {
    vec2 center = gl_PointCoord - vec2(0.5);

    // Stretched horizontally for streak effect
    float dist = length(center * vec2(1.0, 2.0 + vStretch * 4.0));
    if (dist > 0.5) discard;

    float brightness = smoothstep(0.5, 0.1, dist);
    vec3 color = mix(vec3(0.6, 0.8, 1.0), vec3(1.0, 1.0, 1.0), brightness);
    gl_FragColor = vec4(color, vAlpha * brightness);
  }
`;
