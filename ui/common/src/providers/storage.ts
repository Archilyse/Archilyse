export default {
  get: key => {
    return window.localStorage.getItem(key);
  },
  set: (key, value) => {
    window.localStorage.setItem(key, value);
  },
  delete: key => {
    window.localStorage.removeItem(key);
  },
  clear: () => {
    window.localStorage.clear();
  },
};
