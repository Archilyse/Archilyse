module.exports = {
  preset: 'ts-jest',
  moduleNameMapper: {
    '\\.(scss|css|less|png|jpg|gif)$': 'identity-obj-proxy',
    '^archilyse-ui-components$': '<rootDir>/../common/src',
    '^react-planner$': '<rootDir>/src/index',
  },
  transform: {
    '\\.jsx?$': 'babel-jest',
  },
  globals: {
    'ts-jest': {
      babelConfig: true,
      tsconfig: 'jest.tsconfig.json',
    },
    sa_event: () => {},
    React: {},
  },
  testEnvironment: 'jsdom',
  resolver: '<rootDir>/jest_worker_resolver.js',
  setupFilesAfterEnv: ['./setupJest.ts'],
  testTimeout: 10000,
  collectCoverage: true,
  coveragePathIgnorePatterns: ['/node_modules/'],
  coverageReporters: ['json', 'lcov', 'text', 'text-summary'],
};
