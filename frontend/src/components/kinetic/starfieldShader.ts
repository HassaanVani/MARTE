export const starfieldVertexShader = /* glsl */ `
  #include <common>
  #include <logdepthbuf_pars_vertex>
  uniform float uBeta;
  uniform float uGamma;
  uniform vec3 uVelocityDir;
  uniform vec3 uShipPosition;
  uniform float uTime;

  attribute vec3 aOffset;
  attribute float aSize;
  attribute vec3 aColor;
  attribute float aBrightness;
  attribute float aTemperature;

  varying vec3 vColor;
  varying float vAlpha;
  varying vec2 vUv;

  vec3 wavelengthToRGB(float wl) {
    if (wl < 380.0 || wl > 780.0) {
      float fade = 0.0;
      if (wl >= 350.0 && wl < 380.0) fade = (wl - 350.0) / 30.0;
      else if (wl > 780.0 && wl <= 830.0) fade = (830.0 - wl) / 50.0;
      if (fade <= 0.0) return vec3(0.0);
      float edgeWl = wl < 380.0 ? 380.0 : 780.0;
      return wavelengthToRGB(edgeWl) * fade;
    }
    vec3 rgb = vec3(0.0);
    if (wl < 440.0) { rgb.r = -(wl - 440.0) / (440.0 - 380.0); rgb.b = 1.0; }
    else if (wl < 490.0) { rgb.g = (wl - 440.0) / (490.0 - 440.0); rgb.b = 1.0; }
    else if (wl < 510.0) { rgb.g = 1.0; rgb.b = -(wl - 510.0) / (510.0 - 490.0); }
    else if (wl < 580.0) { rgb.r = (wl - 510.0) / (580.0 - 510.0); rgb.g = 1.0; }
    else if (wl < 645.0) { rgb.r = 1.0; rgb.g = -(wl - 645.0) / (645.0 - 580.0); }
    else { rgb.r = 1.0; }
    float factor = 1.0;
    if (wl < 420.0) factor = 0.3 + 0.7 * (wl - 380.0) / (420.0 - 380.0);
    else if (wl > 700.0) factor = 0.3 + 0.7 * (780.0 - wl) / (780.0 - 700.0);
    return rgb * factor;
  }

  void main() {
    vUv = uv;

    vec3 relPos = aOffset - uShipPosition;
    vec3 wrappedPos = mod(relPos + 10000.0, 20000.0) - 10000.0;
    
    vec3 dir = normalize(wrappedPos);
    float radius = length(wrappedPos);

    float maxDist = max(max(abs(wrappedPos.x), abs(wrappedPos.y)), abs(wrappedPos.z));
    float edgeFade = 1.0 - smoothstep(8000.0, 10000.0, maxDist);

    float cosTheta = dot(dir, uVelocityDir);
    float denom = max(1.0 - uBeta * cosTheta, 0.001);
    float cosThetaPrime = clamp((cosTheta - uBeta) / denom, -1.0, 1.0);

    float doppler = 1.0 / max(uGamma * denom, 0.01);
    doppler = clamp(doppler, 0.02, 50.0);

    float beaming = clamp(doppler * doppler * doppler, 0.005, 100.0);

    float sinTheta = sqrt(max(0.0, 1.0 - cosTheta * cosTheta));
    float sinThetaPrime = sqrt(max(0.0, 1.0 - cosThetaPrime * cosThetaPrime));

    vec3 aberratedDir;
    if (sinTheta > 0.001) {
      vec3 perpDir = (dir - cosTheta * uVelocityDir) / sinTheta;
      aberratedDir = cosThetaPrime * uVelocityDir + sinThetaPrime * perpDir;
    } else {
      aberratedDir = sign(cosTheta) * uVelocityDir;
    }

    vec3 aberratedPos = aberratedDir * radius;

    // Ignore instanceMatrix to avoid uninitialized zeroes on some R3F configs
    vec4 mvPosition = modelViewMatrix * vec4(aberratedPos, 1.0);

    // Desired visual size on screen in "pixels"
    float targetSize = aSize * (1.0 + beaming * 0.5);
    targetSize = clamp(targetSize, 1.5, 30.0);

    // Scale by distance to counteract perspective projection so the star 
    // maintains a constant pixel-like size on screen.
    // For fov=75, screen height~1080, factor is roughly 0.002.
    if (mvPosition.z < 0.0) {
      float perspectiveScale = -mvPosition.z * 0.002;
      mvPosition.xy += position.xy * targetSize * perspectiveScale;
    } else {
      mvPosition.xy = vec2(0.0); // Collapse if behind camera
    }

    gl_Position = projectionMatrix * mvPosition;

    float peakWavelength = 2898000.0 / max(aTemperature, 1000.0);
    float shiftedWavelength = peakWavelength / doppler;
    vec3 dopplerColor = wavelengthToRGB(shiftedWavelength);

    float spectralWeight = smoothstep(0.05, 0.3, uBeta);
    vec3 baseColor = mix(aColor, dopplerColor, spectralWeight);
    vColor = baseColor * beaming * (1.0 + aBrightness * 2.0);
    float colorMag = max(max(vColor.r, vColor.g), vColor.b);
    vAlpha = clamp(beaming * (0.5 + aBrightness) + colorMag * 0.5, 0.4, 1.0) * edgeFade;
    
    #include <logdepthbuf_vertex>
  }
`;

export const starfieldFragmentShader = /* glsl */ `
  #include <common>
  #include <logdepthbuf_pars_fragment>

  varying vec3 vColor;
  varying float vAlpha;
  varying vec2 vUv;

  void main() {
    #include <logdepthbuf_fragment>
    
    vec2 center = vUv - vec2(0.5);
    float dist = length(center);
    if (dist > 0.5) discard;

    float core = smoothstep(0.5, 0.05, dist);
    float halo = smoothstep(0.5, 0.3, dist) * 0.3;
    float brightness = core + halo;

    gl_FragColor = vec4(vColor * brightness, vAlpha * brightness);
  }
`;
