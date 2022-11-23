global.console = {
  ...global.console,
  error: jest.fn(),
};

require('@testing-library/jest-dom');
require('jest-fetch-mock').enableMocks();
