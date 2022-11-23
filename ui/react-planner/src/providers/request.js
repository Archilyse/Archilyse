import cookie from 'js-cookie';
import axios from 'axios';

const AUTH_TOKEN = 'access_token';
const isProd = process.env.NODE_ENV === 'production';
const DEV_PORT = 8000;
const API_TIMEOUT = 180000;

const BASE_API_URL = () => (isProd ? '/api' : `http://localhost:${DEV_PORT}/api`);

const instance = axios.create({
  baseURL: BASE_API_URL(),
  timeout: API_TIMEOUT,
  withCredentials: true,
});

const getAuthHeader = () => {
  const accessToken = cookie.get(AUTH_TOKEN);
  return { Authorization: `Bearer ${accessToken}` };
};

instance.interceptors.request.use(config => {
  config.headers = getAuthHeader();
  return config;
});

export default {
  instance,
  get: async (url, options = {}) => {
    const response = await instance.get(url, options);
    return response && response.data;
  },
  patch: async (url, data) => {
    const response = await instance.patch(url, data);
    return response && response.data;
  },
  post: async (url, data) => {
    const response = await instance.post(url, data);
    return response && response.data;
  },
  put: async (url, data) => {
    const response = await instance.put(url, data);
    return response && response.data;
  },
};
