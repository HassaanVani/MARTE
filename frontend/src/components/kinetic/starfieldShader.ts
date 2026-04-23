export const starfieldVertexShader = /* glsl */ `
  uniform float uBeta;
  uniform float uGamma;
  uniform vec3 uVelocityDir;
  uniform float uTime;

  attribute float aSize;
  attribute vec3 aColor;
  attribute float aBrightness;
  attribute float aTemperature;

  varying vec3 vColor;
  varying float vAlpha;

  // Attempt to convert a blackbody-like temperature (Kelvin) to RGB.
  // Attempt to convert a Doppler-shifted wavelength to a perceived color.
  // Uses a simplified spectral model:
  //   1. Map star temperature → peak emission wavelength via Wien's law
  //   2. Apply Doppler shift: λ' = λ / D
  //   3. Convert shifted wavelength → RGB
  // This naturally produces the VISION.md effects:
  //   - Forward stars blueshift → UV → invisible
  //   - Aft stars redshift → IR → invisible ("red void")

  // Attempt to convert a wavelength (nm) to linear RGB.
  // Based on CIE color matching approximations (Bruton/Wyman).
  vec3 wavelengthToRGB(float wl) {
    // Outside visible range (380-780nm): fade to black
    if (wl < 380.0 || wl > 780.0) {
      // Soft fade at edges rather than hard cutoff
      float fade = 0.0;
      if (wl >= 350.0 && wl < 380.0) fade = (wl - 350.0) / 30.0;
      else if (wl > 780.0 && wl <= 830.0) fade = (830.0 - wl) / 50.0;
      if (fade <= 0.0) return vec3(0.0);
      // Use edge color, faded
      float edgeWl = wl < 380.0 ? 380.0 : 780.0;
      return wavelengthToRGB(edgeWl) * fade;
    }

    vec3 rgb = vec3(0.0);

    if (wl < 440.0) {
      rgb.r = -(wl - 440.0) / (440.0 - 380.0);
      rgb.g = 0.0;
      rgb.b = 1.0;
    } else if (wl < 490.0) {
      rgb.r = 0.0;
      rgb.g = (wl - 440.0) / (490.0 - 440.0);
      rgb.b = 1.0;
    } else if (wl < 510.0) {
      rgb.r = 0.0;
      rgb.g = 1.0;
      rgb.b = -(wl - 510.0) / (510.0 - 490.0);
    } else if (wl < 580.0) {
      rgb.r = (wl - 510.0) / (580.0 - 510.0);
      rgb.g = 1.0;
      rgb.b = 0.0;
    } else if (wl < 645.0) {
      rgb.r = 1.0;
      rgb.g = -(wl - 645.0) / (645.0 - 580.0);
      rgb.b = 0.0;
    } else {
      rgb.r = 1.0;
      rgb.g = 0.0;
      rgb.b = 0.0;
    }

    // Intensity correction at edges of visible spectrum
    float factor = 1.0;
    if (wl < 420.0) factor = 0.3 + 0.7 * (wl - 380.0) / (420.0 - 380.0);
    else if (wl > 700.0) factor = 0.3 + 0.7 * (780.0 - wl) / (780.0 - 700.0);

    return rgb * factor;
  }

  void main() {
    vec3 dir = normalize(position);
    float cosTheta = dot(dir, uVelocityDir);

    // Relativistic aberration
    float denom = 1.0 - uBeta * cosTheta;
    float cosThetaPrime = (cosTheta - uBeta) / max(denom, 0.001);
    cosThetaPrime = clamp(cosThetaPrime, -1.0, 1.0);

    // Doppler factor: D = 1 / (γ(1 - β·cos θ))
    float doppler = 1.0 / max(uGamma * denom, 0.01);
    doppler = clamp(doppler, 0.02, 50.0);

    // Relativistic beaming: intensity ∝ D³
    float beaming = doppler * doppler * doppler;
    beaming = clamp(beaming, 0.005, 100.0);

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

    // --- Spectral Doppler shift ---
    // Wien's displacement: peak wavelength (nm) = 2.898e6 / T(K)
    float peakWavelength = 2898000.0 / max(aTemperature, 1000.0);
    // Doppler-shifted wavelength: λ' = λ / D
    float shiftedWavelength = peakWavelength / doppler;
    // Convert to RGB
    vec3 dopplerColor = wavelengthToRGB(shiftedWavelength);

    // Blend: at low β use original star color, at high β use spectral model
    float spectralWeight = smoothstep(0.05, 0.3, uBeta);
    vec3 baseColor = mix(aColor, dopplerColor, spectralWeight);

    // Apply beaming with brightness variation
    vColor = baseColor * beaming * (0.5 + aBrightness * 1.5);

    // Stars shifted outside visible range naturally fade out via wavelengthToRGB
    // returning vec3(0), creating the "red void" aft and "blue point" forward
    float colorMag = max(max(vColor.r, vColor.g), vColor.b);
    vAlpha = clamp(beaming * aBrightness * (0.3 + colorMag * 0.7), 0.0, 1.0);

    vec4 mvPosition = modelViewMatrix * vec4(aberratedPos, 1.0);
    gl_Position = projectionMatrix * mvPosition;

    float basePtSize = aSize * (400.0 / -mvPosition.z);
    gl_PointSize = basePtSize * (0.5 + beaming * 0.5);
    gl_PointSize = clamp(gl_PointSize, 0.8, 14.0);
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
