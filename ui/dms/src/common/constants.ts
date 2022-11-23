import DataViewType from './types/DataViewType';

const isProd = process.env.NODE_ENV === 'production';

export default {
  SERVER_BASENAME: 'dms',

  USER_MANUAL_ADDRESS: 'https://www.archilyse.com/dms-user-manual/',
  // @TODO: Use fn instead of constants for consistency with the dashboard
  URLS: {
    BASE_PATH: '/dms',
    SLAM_PRODUCTION_HOST: '/api',
    SLAM_DEV_SERVICE_HOST: '/api',
    LOCALHOST: 'localhost',
    ASSETS_PATH: () => 'dms-assets',
    LOGIN: () => '/login',
    FORGOT_PASSWORD: () => '/password/forgot',
    CLIENTS: () => '/clients',
    SITES_BY_CLIENT: clientId => `/sites?client_id=${clientId}`,
    BUILDINGS_BY_SITE: siteId => `/buildings?site_id=${siteId}`,
    FLOORS_BY_BUILDING: buildingId => `/floors?building_id=${buildingId}`,
    UNITS_BY_FLOOR: floorId => `/units?floor_id=${floorId}`,
    ROOMS_BY_UNIT: unitId => `/rooms?unit_id=${unitId}`,
    ROOM: (roomId, unitId) => `/room?area_id=${roomId}&unit_id=${unitId}`,
    CUSTOM_FOLDERS: customFolderId => `/custom_folder?folder_id=${customFolderId}`,
    PROFILE: () => '/profile',
    TRASH_BY_CLIENT: clientId => `/trash?client_id=${clientId}`,
    DASHBOARD_PROJECTS: siteId =>
      isProd ? `/dashboard/projects?site_id=${siteId}` : `http://localhost:8080/dashboard/projects?site_id=${siteId}`,
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
    VIEW: 'view',
    PREVIOUS_ROUTE: 'previous_route',
  },
  ROLES: {
    ADMIN: 'ADMIN',
    ARCHILYSE_ONE_ADMIN: 'ARCHILYSE_ONE_ADMIN',
    DMS_LIMITED: 'DMS_LIMITED',
  } as const,
  STATUS: {
    UNPROCESSED: 'UNPROCESSED',
    PENDING: 'PENDING',
    PROCESSING: 'PROCESSING',
    SUCCESS: 'SUCCESS',
    FAILURE: 'FAILURE',
  },
  DMS_PERMISSIONS: {
    // UI LABEL: BE value
    READ: 'READ',
    EDIT: 'WRITE',
    READ_ALL: 'READ_ALL',
    EDIT_ALL: 'WRITE_ALL',
  } as const,
  ENDPOINTS: {
    BUILDING: buildingId => `/building/${buildingId}`,
    BUILDINGS_BY_SITE: siteId => `/building/?site_id=${siteId}`,
    CLIENT: (clientId = null) => (clientId ? `/client/${clientId}` : '/client/'),
    FILE: (fileId = null) => (fileId ? `/file/${fileId}` : '/file/'),
    FILE_SEARCH: searchFilter => `/file/?${searchFilter}`,
    FILE_DOWNLOAD: fileId => `/file/${fileId}/download`,
    FILE_COMMENTS: fileId => `/file/${fileId}/comment`,
    FILE_TRASH: (fileId = null) => (fileId ? `/file/trash/${fileId}` : '/file/trash'),
    FOLDER: (folderId: string = null): string => (folderId ? `/folder/${folderId}` : '/folder/'),
    FOLDER_FILE_TRASH: (fileId = null) => (fileId ? `/folder/files/trash/${fileId}` : '/files/trash'),
    FOLDER_TRASH: (id: string = null): string => (id ? `/folder/trash/${id}` : '/folder/trash'),
    FOLDER_TRASH_RESTORE: (folderId: string = null): string => `/folder/restore/${folderId}`,
    FOLDER_FILE_SEARCH: (folderId: string = null) => `/folder/${folderId}/files`,
    FOLDER_SEARCH: (searchFilter: string = null) => `/folder/?${searchFilter}`,
    FOLDER_SUBFOLDERS: (folderId: string = null) => `/folder/${folderId}/subfolders`,
    FOLDER_FILES: folderId => `/folder/${folderId}/files`,
    FLOOR: floorId => `/floor/${floorId}`,
    FLOORS_BY_BUILDING: buildingId => `/floor/?building_id=${buildingId}`,
    LOGIN: () => '/auth/login',
    PLAN: planId => `/plan/${planId}`,
    SITE: siteId => `/site/${siteId}`,
    SITES_WITH_READY_BY_CLIENT: clientId => `site/?client_id=${clientId}`,
    SITES_BY_CLIENT: clientId => `site/?client_id=${clientId}&dms_sites=true`,
    SITE_UNITS: siteId => `/site/${siteId}/units`,
    SITE_NET_AREA_DISTRIBUTION: searchFilter => `/site/net-area-distribution?${searchFilter}`,
    ROOMS_BY_UNIT: unitId => `/areas/?unit_id=${unitId}`,
    UNIT: unitId => `/unit/${unitId}`,
    UNIT_FLOOR_PLAN: (unitId, language = 'EN', file_format = 'PNG') =>
      `/unit/${unitId}/deliverable?language=${language}&file_format=${file_format}`,
    UNIT_AREAS: (unitId, areaId) => `/unit/${unitId}/areas/${areaId}`,
    UNITS_BY_FLOOR: floorId => `/unit/?floor_id=${floorId}`,
    USER: (userId = null) => (userId ? `/user/${userId}` : '/user/'),
    USERS_BY_CLIENT: (clientId = null) => `/user/?client_id=${clientId}`,
    USER_DMS_PERMISSIONS: (userId = null) => (userId ? `/user/dms/${userId}` : '/user/dms'),
    USER_ROLES: () => '/user/role',
    USER_RESET_PASSWORD: () => '/user/reset_password',
    USER_FORGOTTEN_PASSWORD: () => '/user/forgot_password',
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
    NET_AREA_DISTRIBUTION: [
      // Generated using https://learnui.design/tools/data-color-picker.html & chroma.js
      '#007cb1',
      '#308db9',
      '#4d9ec1',
      '#68aec9',
      '#82bfd2',
      '#9dcfdb',
      '#b8dfe6',
      '#d3eff2',
      '#bfe4e9',
      '#cfedf0',
      '#def6f7',
      '#eeffff',
    ],
  },

  DELAY_FILTER_MS: 300,

  CUSTOM_FOLDER_TYPE: 'custom-folder',

  DMS_VIEWS: {
    SITES: '/sites',
    CLIENTS: '/clients',
    BUILDINGS: '/buildings',
    FLOORS: '/floors',
    UNITS: '/units',
    ROOMS: '/rooms',
    ROOM: '/room',
    TRASH: '/trash',
    CUSTOM_FOLDER: '/custom_folder',
  } as const,
  VIEWS: DataViewType,

  CSS: {
    MODAL_STYLE: {
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: 'rgba(42, 121, 161, 0.7)',
    } as any,
  },

  // @TODO: Some constants here are duplicated with the ones in dashboard
};
