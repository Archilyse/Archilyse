const isProd = process.env.NODE_ENV === 'production';
const DEV_PORT = 8000;

export default {
  COOKIES: {
    // @TODO: Make this handled by the BE automatically
    AUTH_TOKEN: 'access_token',
    ROLES: 'roles',
  },

  API_TIMEOUT: 180000,
  BASE_API_URL: () => (isProd ? '/api' : `http://localhost:${DEV_PORT}/api`),
  LOGIN: () => '/login',

  ENDPOINTS: {
    AUTHENTICATE: () => `/auth/login`,
    BUILDING: buildingId => `/building/${buildingId}`,
    BUILDING_3D: buildingId => `/building/${buildingId}/3d`,
    UNIT_BROOKS_SIMPLE: unitId => `/unit/${unitId}/brooks/simple`,
    PLAN_BROOKS_SIMPLE: planId => `/plan/${planId}/brooks/simple`,
    UNIT_HEATMAPS: (unitId, simulation_type = null) =>
      `/unit/${unitId}/simulation_results?georeferenced=true${
        simulation_type ? `&simulation_type=${simulation_type}` : ''
      }`,
    SITE_STRUCTURE: siteId => `/site/${siteId}/structure`,
    SITE_UNITS: (siteId, field = null) => (field ? `/site/${siteId}/units?field=${field}` : `/site/${siteId}/units`),
    MANUAL_SURROUNDINGS: siteId => `/manualsurroundings/${siteId}`,
  },

  FADED_UNIT_COLOR: '#d3d3d3',
  DASHBOARD_3D_UNIT_COLOR: 0xaaaaaa,
  DASHBOARD_3D_BACKGROUND: 0xe1ebff,
  HEATMAP_3D_BACKGROUND: 0xececec,
  DEFAULT_3D_BACKGROUND: 0x87959a,
  DASHBOARD_3D_EDGES_COLOR: 0x808080,
  DASHBOARD_3D_EDGES_COLOR_NO_CONTEXT: 0xffffff,
  GEOJSON_MAP_BUILDING_COLOR: '#fdcd14',
  GEOJSON_MAP_EXCLUSION_AREA_COLOR: 'rgb(255,0,0)',
  GEOJSON_MAP_SITE_COLOR: 'rgb(0,0,0)',

  // --- HARPGL  ---
  HARPGL_ACCESS_TOKEN: 'qEcEfaaU4MWYUXeUisqy1XFIFaC8xtTeF6p6FjSdtsE',
  HARPGL_3D_TILES: 'https://vector.hereapi.com/v2/vectortiles/base/mc',
  // All open-source options:
  // berlin_tilezen_base.json
  // berlin_tilezen_day_reduced.json
  // berlin_tilezen_night_reduced.json
  // berlin_tilezen_effects_streets.json
  // berlin_tilezen_effects_outlines.json
  HARPGL_THEME: 'https://unpkg.com/@here/harp-map-theme@0.28.0/resources/berlin_tilezen_base.json',

  // 3d Render modes
  MAP_TILES_TO_DISPLAY: 300,

  // Event constants
  EVENT_KEYDOWN: 'keydown',
  EVENT_KEYUP: 'keyup',
  EVENT_RESIZE: 'resize',

  FONT_FAMILY: 'Barlow',
  COLORS: {
    WEBSITE_BRAND: '#21406c',
    PRIMARY: '#2a79a1',
    PRIMARY_TRANSPARENT: 'rgba(42, 121, 161, 0.7)',
    PRIMARY_VERY_TRANSPARENT: 'rgba(42, 121, 161, 0.1)',
    SECONDARY: '#898989',
    BACKGROUND: '#ececec',
    GREY: '#b5b5b5',
    ICONS_GREY: '#808080',
    LIGHT_GREY: '#c4c4c4',
    ENVELOPE_YELLOW_DARKENED: 'rgba(230, 210, 34)',
    WHITE: '#ffffff',
  },
  ROLES: {
    ADMIN: 'ADMIN',
    COMPETITION_ADMIN: 'COMPETITION_ADMIN',
    COMPETITION_VIEWER: 'COMPETITION_VIEWER',
    TEAMMEMBER: 'TEAMMEMBER',
    ARCHILYSE_ONE_ADMIN: 'ARCHILYSE_ONE_ADMIN',
    DMS_LIMITED: 'DMS_LIMITED',
    TEAMLEADER: 'TEAMLEADER',
    POTENTIAL_API: 'POTENTIAL_API',
  } as const,
};

export const PATRIZIA_SITES_IDS = [2850, 2851, 2852, 2853, 2854];
