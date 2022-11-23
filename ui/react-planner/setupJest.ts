global.console = {
  ...global.console,
  error: jest.fn(),
};

// @ts-ignore
global.sa_event = (eventName, metadata = {}) => {}; // SimpleAnalytics global function to send events

let timeout;
// To mock img on load in modules such as `utils/get-img-dimensions.ts`
global.document.createElement = (function (create) {
  return function (...args) {
    const element: HTMLElement = create.apply(this, args);

    if (element.tagName === 'IMG') {
      clearTimeout(timeout);

      timeout = setTimeout(() => {
        element.onload(new Event('load'));
      }, 100);
    }
    return element;
  };
})(document.createElement);

require('@testing-library/jest-dom');
require('jest-fetch-mock').enableMocks();
