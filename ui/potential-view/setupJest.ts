global.console = {
  ...global.console,
  error: jest.fn(),
};

require('@testing-library/jest-dom');

// has to be here otherwise `arhilyse-ui-components` prints a huge bunch of generated code and tests fail
require('jest-fetch-mock').enableMocks();

const { server } = require('./tests/server-mocks');

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
