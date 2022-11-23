import axios from 'axios';
import { C } from '../common';
import { getAuthHeader } from '../common/modules';

const instance = axios.create({
  baseURL: C.URLS.BASE(),
});

instance.interceptors.request.use(config => {
  config.headers = getAuthHeader();
  return config;
});

const _cache = {};

export default {
  instance,
  async get<T = any>(url: string, options = {}): Promise<T> {
    const response = await instance.get<T>(url, options);
    return response && response.data;
  },
  getCached: async url => {
    // If we already got a value we use it, otherwise we assign the promise.
    let response = _cache[url] ? _cache[url] : instance.get(url);
    _cache[url] = response;

    // If it's a promise we have to wait. But all wait for the same one.
    // Otherwise if Process 1 and process 2 request the same fast, there would be 2 same requests
    // This way both would stay waiting for the first
    if (response && response.then) {
      response = await response;
    }
    return response && response.data;
  },
  async put<T = any>(url: string, data): Promise<T> {
    const response = await instance.put<T>(url, data);
    return response && response.data;
  },
  post: async (url: string, data) => {
    const response = await instance.post(url, data);
    return response && response.data;
  },
  delete: async (url: string) => {
    const response = await instance.delete(url);
    return response && response.data;
  },
};
