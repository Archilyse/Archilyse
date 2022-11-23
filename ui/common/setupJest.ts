import '@testing-library/jest-dom';

global.console = {
  ...global.console,
  error: jest.fn(),
};

global.onmessage = () => {};

const { server } = require('./tests/utils/server-mocks');

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
