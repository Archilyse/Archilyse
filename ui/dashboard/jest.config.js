module.exports = {
  preset: 'ts-jest',
  moduleNameMapper: {
    '\\.(csv)$': '<rootDir>/__mocks__/csvMock.js',
    '\\.(scss|css|less|png|gif)$': 'identity-obj-proxy',
    '^archilyse-ui-components$': '<rootDir>/../common/src',
  },
  globals: {
    'ts-jest': {
      babelConfig: true,
      tsconfig: 'jest.tsconfig.json',
    },
    React: {},
  },
  testEnvironment: 'jsdom',
  resolver: '<rootDir>/jest_worker_resolver.js',
  setupFilesAfterEnv: ['./setupJest.ts'],
  testTimeout: 10000,
  testPathIgnorePatterns: ['.spec'],
  coverageReporters: [
    "json",
    "text-summary"
  ]
};
