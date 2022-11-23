export const environment = {
  production: true,

  apiPlanUrl: '/api/plan/',
  apiFloorUrl: '/api/floor/',
  apiBuildingUrl: '/api/building/',
  apiAnnotationUrl: '/api/annotation/',
  apiUnitUrl: '/api/unit/',
  apiConstantsUrl: '/api/constants/',
  apiPotentialUrl: '/api/potential/',
  apiFeaturesUrl: '/api/features/',
  apiSiteUrl: '/api/site/',

  /*
  Platform login
  */
  apiAuthUrl: '/api/auth/login',

  apiQaUrl: '/api/qa/',

  adminBuildingsUrl: 'https://slam.archilyse.com/admin/buildings?site_id=',

  sentryDSN: 'https://199d5e83aca842a396f682962c06d854@sentry.io/1731932',
  googleTrackingId: 'UA-109816142-3',

  mapboxToken: 'pk.eyJ1IjoibGVzejNrIiwiYSI6ImNra3FyMHlmOTBoY28ydXBmc3Vzb2t0cjYifQ.PGuiWX9XwpBkCgC6FdbceA',

  /** Display detailed errors in the console, for debug only */
  displayErrors: false,

  /** QA error detecting parameters */
  qaErrorMarginM2: 0.03,
  qaErrorMarginRooms: 0.5,

  /** dashboardURL */
  dashboardURL: 'https://app.archilyse.com',
};
