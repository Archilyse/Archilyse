import axios from 'axios';
import cookie from 'js-cookie';
import { C } from '../common';

const isProd = process.env.NODE_ENV === 'production';

export const getUrlForRequests = () => {
  // Client side
  if (isProd) return '/api';
  return `http://${C.URLS.LOCALHOST}:${C.PORTS.LOCAL_DEV}/api`;
};

const getAuthHeader = () => {
  const accessToken = cookie.get(C.COOKIES.AUTH_TOKEN);
  return { Authorization: `Bearer ${accessToken}` };
};

const instance = axios.create({
  baseURL: getUrlForRequests(),
  withCredentials: true,
});

instance.interceptors.request.use(config => {
  config.headers = getAuthHeader();
  return config;
});

const getFormData = (data: any) => {
  const formData = new FormData();
  Object.keys(data).forEach(key => {
    const value = data[key];
    if (value instanceof FileList) {
      Array.from(value).forEach(file => {
        formData.append(key, file);
      });
    } else {
      formData.append(key, value);
    }
  });
  return formData;
};

export default {
  instance,
  get: async url => {
    const response = await instance.get(url);
    return response && response.data;
  },
  put: async (url, data) => {
    const response = await instance.put(url, data);
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
  multipart: async (url, data) => {
    const formData = getFormData(data);
    const response = await instance.post(url, formData, {
      headers: {
        'content-type': 'multipart/form-data',
      },
    });

    return response && response.data;
  },
  delete: async url => {
    const response = await instance.delete(url);
    return response;
  },
  getFiles: async (url, type) => {
    const response = await instance.get(url, { responseType: type });
    return response && response.data;
  },
};
