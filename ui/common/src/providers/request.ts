import axios, { AxiosRequestConfig } from 'axios';
import cookie from 'js-cookie';
import C from '../constants';

const CACHE_DURATION_MS = 20 * 60 * 1000; // 20 min

const getAuthHeader = () => {
  const accessToken = cookie.get(C.COOKIES.AUTH_TOKEN);
  return { Authorization: `Bearer ${accessToken}` };
};

const instance = axios.create({
  baseURL: C.BASE_API_URL(),
  timeout: C.API_TIMEOUT,
});

instance.interceptors.request.use(config => {
  config.headers = getAuthHeader();
  return config;
});

let _cache = {};

const clearCache = () => {
  _cache = {};
};

setInterval(clearCache, CACHE_DURATION_MS);

export default {
  instance,
  get: async url => {
    const response = await instance.get(url);
    return response && response.data;
  },
  getCached: async (url, options: AxiosRequestConfig = undefined) => {
    // If we already got a value we use it, otherwise we assign the promise.
    let response = _cache[url] ? _cache[url] : instance.get(url, options);

    // If it's a promise we have to wait. But all wait for the same one.
    // Otherwise if Process 1 and process 2 request the same fast, there would be 2 same requests
    // This way both would stay waiting for the first
    if (response && response.then) {
      response = await response;
    }
    _cache[url] = response;
    return response && response.data;
  },
  put: async (url, data) => {
    const response = await instance.put(url, data);
    return response && response.data;
  },
  post: async (url, data) => {
    const response = await instance.post(url, data);
    return response && response.data;
  },
  delete: async url => {
    const response = await instance.delete(url);
    return response && response.data;
  },
};
