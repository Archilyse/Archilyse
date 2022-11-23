global.console = {
  ...global.console,
  error: jest.fn(),
};

require('@testing-library/jest-dom');
require('jest-fetch-mock').enableMocks();

const { server } = require('./tests/utils/server-mocks');

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
