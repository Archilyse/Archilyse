module.exports = {
  preset: 'ts-jest',
  moduleNameMapper: {
    '\\.(scss|css|less|png|gif)$': 'identity-obj-proxy',
    '^Common(.*)$': '<rootDir>/src/common$1',
    '^Providers(.*)$': '<rootDir>/src/providers$1',
    '^Components(.*)$': '<rootDir>/src/components$1',
    '^archilyse-ui-components$': '<rootDir>/../common/src',
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
