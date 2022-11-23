const isProd = process.env.NODE_ENV === 'production';
const DEV_PORT = 8000;

export default {
  SERVER_BASENAME: 'dashboard',

  SWISS_GERMAN_LOCALE: 'de-CH',

  ROUNDING_M2_PRICE: 'M2_PRICE',
  ROUNDING_PRICE: 'PRICE',
  COMPETITION_USER_MANUAL_ADDRESS: 'https://www.archilyse.com/competition-tool-user-manual/',

  ENDPOINTS: {
    AUTHENTICATE: () => `/auth/login`,
    CLIENT: clientId => `/client/${clientId}`,
    FLOOR: floorId => `floor/${floorId}`,
    FLOORS_BY_PLAN: planId => `floor/?plan_id=${planId}`,
    PLAN: planId => `/plan/${planId}`,
    PLAN_RAW_IMAGE: planId => `/plan/${planId}/raw_image`,
    SITE: siteId => `/site/${siteId}`,
    SITE_STRUCTURE: siteId => `/site/${siteId}/structure`,
    SITE_UNITS: (siteId, field = null) => (field ? `/site/${siteId}/units?field=${field}` : `/site/${siteId}/units`),
    SITE_SIM_VALIDATION: siteId => `/site/${siteId}/sim_validation`,
    UNIT_HEATMAPS: (unitId, simulation_type = null) =>
      `/unit/${unitId}/simulation_results?georeferenced=true${
        simulation_type ? `&simulation_type=${simulation_type}` : ''
      }`,
    COMPETITIONS: () => '/competition/competitions',
    COMPETITION_CATEGORIES: id => `/competition/${id}/categories`,
    COMPETITION_COMPETITORS: competitionId => `/competition/${competitionId}/competitors`,
    COMPETITION_COMPETITOR_CLIENT_INPUT: (competitionId, competitorId = null) =>
      `/competition/${competitionId}/competitors/${competitorId}/manual_input`,
    COMPETITION_COMPETITORS_UNITS: competitionId => `/competition/${competitionId}/competitors/units`,
    COMPETITION_SCORES: id => `/competition/${id}/scores`,
    COMPETITION_INFO: id => `/competition/${id}/info`,
    COMPETITION_WEIGHTS: id => `/competition/${id}/weights`,
    COMPETITION_PARAMETERS: id => `/competition/${id}/configuration_parameters`,
  },

  URLS: {
    BASE: () => (isProd ? '/api' : `http://localhost:${DEV_PORT}/api`),
    ARCHILYSE_CONTACT: () => 'https://www.archilyse.com/contact/',
    LOGIN: () => '/login',
    QA: siteId => `/qa/${siteId}`,
    COMPETITION: (id = null) => (id ? `/competition/${id}` : '/competition'),
    COMPETITIONS: () => `/competitions`,
  },
  COOKIES: {
    // @TODO: Make this handled by the BE automatically
    AUTH_TOKEN: 'access_token',
    ROLES: 'roles',
  },

  ROLES: {
    ADMIN: 'ADMIN',
    COMPETITION_ADMIN: 'COMPETITION_ADMIN',
    COMPETITION_VIEWER: 'COMPETITION_VIEWER',
  } as const,

  FONT_FAMILY: 'Barlow',
  COLORS: {
    PRIMARY: '#2a79a1',
    PRIMARY_TRANSPARENT: 'rgba(42, 121, 161, 0.7)',
    PRIMARY_VERY_TRANSPARENT: 'rgba(42, 121, 161, 0.1)',
    SECONDARY: '#898989',
    BACKGROUND: '#ececec',
    GREY: '#b5b5b5',
    LIGHT_GREY: '#c4c4c4',
    WHITE: '#ffffff',
  },

  QA_COLOR_SCALE: [
    '#0d47a1',
    '#1565c0',
    '#1976d2',
    '#1e88e5',
    '#2196f3',
    '#42a5f5',
    '#64b5f6',
    '#90caf9',
    '#bbdefb',
    '#cad9e4',
    '#b0bfcA',
  ],

  CSS: {
    MODAL_STYLE: {
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: 'rgba(42, 121, 161, 0.7)',
    } as any,
  },
};
