export default {
  SERVER_BASENAME: 'admin',

  // @TODO: Use fn instead of constants for consistency with the dashboard
  URLS: {
    BASE_PATH: '/admin',
    SLAM_PRODUCTION_HOST: '/api',
    SLAM_DEV_SERVICE_HOST: '/api',
    LOCALHOST: 'localhost',
    ASSETS_PATH: () => 'admin-ui-assets',
    LOGIN: () => '/login',
    FORGOT_PASSWORD: () => '/password/forgot',
    CLIENTS: () => '/clients',
    SITES_BY_CLIENT: clientId => `/sites?client_id=${clientId}`,
    COMPETITIONS_BY_CLIENT: clientId => `/competitions?client_id=${clientId}`,
    BUILDINGS_BY_SITE: siteId => `/buildings?site_id=${siteId}`,
    FLOORS_BY_BUILDING: buildingId => `/floors?building_id=${buildingId}`,
    UNITS_BY_FLOOR: floorId => `/units?floor_id=${floorId}`,
    ROOMS_BY_UNIT: unitId => `/rooms?unit_id=${unitId}`,
    PLAN: planId => `/floor/plan?plan_id=${planId}`,
    CUSTOM_FOLDERS: customFolderId => `/custom_folder?folder_id=${customFolderId}`,
    PROFILE: () => '/profile',
    PIPELINES: () => '/pipelines',
    QA_TEMPLATE: () => `/qa/template`,
    QA_TEMPLATE_HEADERS: () => `/qa/template_headers`,
    EDITOR: plan_id => `/v2/editor/${plan_id}`,
    COMPETITION_TOOL: competitionId => `/dashboard/competition/${competitionId}`,
    PIPELINE: {
      LABELLING: (planId: number) => `/v2/editor/${planId}`,
      CLASSIFICATION: (planId: number) => `/classification/${planId}`,
      GEOREFERENCE: (planId: number) => `/georeference/${planId}`,
      SPLITTING: (planId: number) => `/splitting/${planId}`,
      LINKING: (planId: number) => `/linking/${planId}`,
    },
  },
  PORTS: {
    LOCAL_DEV: 8000, // Change to 80 if we run 'make up'
  },
  TOOLTIPS: {
    QA: 'QA is not available until the site is labelled or hidden when delivered for non admins',
    PIPELINES: 'Pipelines are not visible when the site is delivered for non admins',
    SIMULATIONS: 'Heatmaps & simulations (only available if site is simulated)',
    BUILDINGS: 'Buildings are not visible when the site is delivered for non admins',
    EDIT: 'Edition is not actionable when the site is delivered for non admins',
  },
  COOKIES: {
    // @TODO: This is probably only needed in development right now, remove it.
    AUTH_TOKEN: 'access_token',
    ROLES: 'roles',
  },
  STORAGE: {
    TABLE_SEARCH: fullPath => `table_search_for_${fullPath}`,
    VIEW: 'view',
    PREVIOUS_ROUTE: 'previous_route',
  },
  ROLES: {
    ADMIN: 'ADMIN',
    TEAMMEMBER: 'TEAMMEMBER',
    TEAMLEADER: 'TEAMLEADER',
  } as const,
  STATUS: {
    UNPROCESSED: 'UNPROCESSED',
    PENDING: 'PENDING',
    PROCESSING: 'PROCESSING',
    SUCCESS: 'SUCCESS',
    FAILURE: 'FAILURE',
  },
  ENDPOINTS: {
    BUILDING: buildingId => `/building/${buildingId}`,
    BUILDINGS_BY_SITE: siteId => `/building/?site_id=${siteId}`,
    CLASSIFICATION_SCHEMES: () => '/constants/classification_schemes',
    CLIENT: (clientId = null) => (clientId ? `/client/${clientId}` : '/client/'),
    COMPETITIONS_BY_CLIENT: clientId => `/competition/?client_id=${clientId}`,
    COMPETITION_ADMIN: competitionId => `/competition/${competitionId}`,
    COMPETITION_CATEGORIES: () => `/competition/categories`,
    FLOOR: (floorId = null) => (floorId ? `/floor/${floorId}` : '/floor/'),
    FLOORS_BY_BUILDING: buildingId => `/floor/?building_id=${buildingId}`,
    GROUP: () => '/group/',
    LOGIN: () => '/auth/login',
    PIPELINE_FOR_PLAN: planId => `/plan/${planId}/pipeline`,
    PIPELINE_FOR_SITE: siteId => `/site/${siteId}/pipeline`,
    PLAN: planId => `/plan/${planId}`,
    SET_MASTERPLAN: planId => `/plan/${planId}/masterplan`,
    RAW_PLAN_IMAGE: planId => `plan/${planId}/raw_image`,
    QA_BY_CLIENT_SITE_ID: (clientSiteId, clientId) => `qa/?client_site_id=${clientSiteId}&client_id=${clientId}`,
    QA_BY_SITE: siteId => `/qa/?site_id=${siteId}`,
    QA: (qaId = null) => (qaId ? `/qa/${qaId}` : `/qa/`),
    SITE_RUN_FEATURES: siteId => `/site/${siteId}/run-feature-generation`,
    SITE: () => `site/`,
    SITE_NAMES: clientId => `/site/names?client_id=${clientId}`,
    SITE_BY_ID: (siteId, withLatLon = false) => (withLatLon ? `/site/${siteId}?withLatLon=true` : `/site/${siteId}`),
    SITES_WITH_READY_BY_CLIENT: clientId => `site/?client_id=${clientId}`,
    SITE_UNITS: siteId => `/site/${siteId}/units`,
    SITE_NET_AREA_DISTRIBUTION: searchFilter => `/site/net-area-distribution?${searchFilter}`,
    UNIT: unitId => `/unit/${unitId}`,
    UNITS_BY_FLOOR: floorId => `/unit/?floor_id=${floorId}`,
    USER: (userId = null) => (userId ? `/user/${userId}` : '/user/'),
    USERS_BY_CLIENT: (clientId = null) => `/user/?client_id=${clientId}`,
    USER_DMS_PERMISSIONS: (userId = null) => (userId ? `/user/dms/${userId}` : '/user/dms'),
    USER_ROLES: () => '/user/role',
    USER_RESET_PASSWORD: () => '/user/reset_password',
    USER_FORGOTTEN_PASSWORD: () => '/user/forgot_password',
    UNITS_SUMMARY_BY_FLOOR: (planId, floorId) => `/plan/${planId}/units?floor_id=${floorId}`,
    SITE_UPLOAD_PH_RESULTS: siteId => `/site/${siteId}/ph-results`,
    MANUAL_SURROUNDINGS: siteId => `/manualsurroundings/${siteId}`,
    SITE_GEOREF_PLANS: siteId => `/site/${siteId}/ground_georef_plans`,
    SITE_TASK_ALL_DELIVERABLES: siteId => `/site/${siteId}/task/all_deliverables`,
    SITE_TASK_GENERATE_IFC_FILE_TASK: siteId => `/site/${siteId}/task/generate_ifc_file_task`,
    SITE_TASK_GENERATE_UNIT_PLOTS_TASK: siteId => `/site/${siteId}/task/generate_unit_plots_task`,
    SITE_TASK_GENERATE_VECTOR_FILES_TASK: siteId => `/site/${siteId}/task/generate_vector_files_task`,
    SITE_TASK_GENERATE_ENERGY_REFERENCE_AREA: siteId => `/site/${siteId}/task/generate_energy_reference_area_task`,
    SITE_TASK_SLAM_RESULTS_SUCCESS: siteId => `/site/${siteId}/task/slam_results_success`,
  },
  MIME_TYPES: {
    CSV: 'text/csv',
    EXCEL_OLD: 'application/vnd.ms-excel',
    EXCEL_NEW: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ZIP: 'application/zip',
    PDF: 'application/pdf',
    PNG: 'image/png',
    JPEG: 'image/jpeg',
  },
  FILE_EXTENSIONS: {
    DXF: '.dxf',
    IFC: '.ifc',
  },
  RESPONSE_TYPE: {
    TEXT: 'text',
    ARRAY_BUFFER: 'arraybuffer',
  },
  FORMS: {
    EMPTY_LABEL: '<none>',
  },
  COLORS: {
    // @TODO: Use a common constants file with the dashboard
    GREY: 'grey',
    WHITE: 'white',
    SECONDARY: '#898989',
    HOVERED_COLOR: '#9494942e',
    PRIMARY_COLOR: '#2a79a1',
    BRAND_COLOR: '#21406c',
    TAGS: ['#FFAC4A', '#30A8FF', '#F85461', '#6BB685', '#277095'],
  },
  CSS: {
    // @TODO: To common
    MODAL_STYLE: {
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: 'rgba(42, 121, 161, 0.7)',
    } as any,
  },
  DELAY_FILTER_MS: 300,

  // @TODO: Some constants here are duplicated with the ones in dashboard
};
