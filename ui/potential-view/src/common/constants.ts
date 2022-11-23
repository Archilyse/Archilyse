export default {
  URLS: {
    BASE_PATH: () => '/v2/viewer',
    HOME: () => '/',
    LOGIN: () => '/login',
    SIMULATION_VIEW: id => `/${id}`,
    LOCALHOST: 'localhost',
  } as const,

  ENDPOINTS: {
    SIMULATIONS_LIST: () => '/potential/simulations',
    SIMULATION: id => `/potential/simulations/${id}`,
    SIMULATION_RESULT: id => `/potential/simulations/${id}/result`,
  },

  ROLES: {
    ADMIN: 'ADMIN',
    POTENTIAL_API: 'POTENTIAL_API',
  } as const,

  COOKIES: {
    AUTH_TOKEN: 'access_token',
    ROLES: 'roles',
  } as const,
  PORTS: {
    LOCAL_DEV: 8000, // Change to 80 if we run 'make up'>
  },
};
