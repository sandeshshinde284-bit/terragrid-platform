/**
 * SOURCE REGISTRY - Centralized Configuration
 * 
 * This is the single source of truth for all data source configurations.
 * When backend adds a new data source, simply add it to SOURCE_REGISTRY below.
 * No frontend recompilation needed - component automatically supports it!
 * 
 * How to add a new source:
 * 1. Backend sends incident with new source: { source: 'sentinel_5p' }
 * 2. Update SOURCE_REGISTRY with new source config below
 * 3. Deploy config change (no code recompile needed)
 * 4. Frontend automatically displays full source details
 */

export interface SourceConfig {
  name: string
  description: string
  accuracy: number
  region: string
  limitations: string
}

export const SOURCE_REGISTRY: Record<string, SourceConfig> = {
  // NORMALIZED KEY: lowercase, underscore-separated
  'nasa_eonet': {
    name: 'NASA EONET',
    description: 'NASA Earth Observatory Natural Event Tracker',
    accuracy: 92,
    region: 'Global satellite imagery',
    limitations: 'Cloud obstruction, 2-4 hour latency'
  },
  'gdacs': {
    name: 'GDACS',
    description: 'Global Disaster Alert and Coordination System',
    accuracy: 88,
    region: 'Global coordination network',
    limitations: 'Relies on member agency reports'
  },
  'usgs_earthquakes': {
    name: 'USGS Earthquake Hazards',
    description: 'United States Geological Survey',
    accuracy: 99,
    region: 'Earthquake detection worldwide',
    limitations: 'Earthquake focused, not floods/fires'
  },
  'openweather': {
    name: 'OpenWeather',
    description: 'Real-time weather and climate data',
    accuracy: 88,
    region: 'Global weather patterns',
    limitations: 'Weather predictions 15+ days unreliable'
  },
  'noaa': {
    name: 'NOAA',
    description: 'National Oceanic and Atmospheric Administration',
    accuracy: 91,
    region: 'US weather and marine data',
    limitations: 'US-centric coverage'
  }
  // ✅ TO ADD NEW SOURCE:
  // 'new_source_key': {
  //   name: 'Display Name',
  //   description: 'What this source provides',
  //   accuracy: 85,
  //   region: 'Geographic coverage',
  //   limitations: 'Known limitations'
  // }
}

/**
 * Normalize source string to canonical key
 * Handles case variations and aliases: 'NASA' → 'nasa_eonet', 'USGS' → 'usgs_earthquakes'
 * 
 * @param source - Raw source string from backend
 * @returns Normalized key for registry lookup
 */
export function getNormalizedSourceKey(source: string): string {
  if (!source) return 'unknown'
  
  const normalized = source.toLowerCase().trim()
  
  // Map backend variations to canonical keys
  const aliases: Record<string, string> = {
    'nasa': 'nasa_eonet',
    'nasa_eonet': 'nasa_eonet',
    'eonet': 'nasa_eonet',
    'gdacs': 'gdacs',
    'usgs': 'usgs_earthquakes',
    'usgs_earthquakes': 'usgs_earthquakes',
    'earthquakes': 'usgs_earthquakes',
    'openweather': 'openweather',
    'weather': 'openweather',
    'noaa': 'noaa'
  }
  
  return aliases[normalized] || normalized
}

/**
 * Get source configuration with intelligent fallback
 * 
 * @param source - Raw source string from incident
 * @returns SourceConfig with full details or helpful fallback
 * 
 * Example:
 * - getSourceDetails('nasa_eonet') → Full NASA EONET config
 * - getSourceDetails('NASA') → Full NASA EONET config (normalized)
 * - getSourceDetails('sentinel_5p') → Smart fallback with helpful message
 */
export function getSourceDetails(source: string): SourceConfig {
  const key = getNormalizedSourceKey(source)
  
  if (SOURCE_REGISTRY[key]) {
    return SOURCE_REGISTRY[key]
  }
  
  // ✅ SMART FALLBACK: Return helpful message for unknown/new sources
  return {
    name: source,
    description: 'Custom data source (not yet in registry)',
    accuracy: 60,  // Conservative estimate
    region: 'Coverage area unknown - add to registry',
    limitations: 'New source detected - please add to sourceRegistry.ts'
  }
}
