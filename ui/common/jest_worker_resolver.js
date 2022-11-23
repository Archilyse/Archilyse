const url = require('url');

module.exports = (request, options) => {
  // Remove any query parameters in the request path
  // (e.g. ?worker, which Vite uses for worker imports), related: https://github.com/vitejs/vite/discussions/5552
  if (request.includes('?')) {
    return options.defaultResolver(url.parse(request).pathname, options);
  }

  return options.defaultResolver(request, options);
};
