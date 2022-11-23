module.exports = {
  preset: 'ts-jest',
  moduleNameMapper: {
    '\\.(csv)$': '<rootDir>/__mocks__/csvMock.js',
    '\\.(scss|css|less|png|gif)$': 'identity-obj-proxy',
  },
  globals: {
    'ts-jest': {
      babelConfig: true,
      tsconfig: 'jest.tsconfig.json',
    },
    React: {},
  },
  resolver: '<rootDir>/jest_worker_resolver.js',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['./setupJest.ts'],
  testTimeout: 10000,
  testPathIgnorePatterns: ['.spec'],
  collectCoverage: true,
  coveragePathIgnorePatterns: ['/node_modules/'],
  coverageReporters: ['json', 'lcov', 'text', 'text-summary'],
};
