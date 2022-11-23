import { getCommonEnvironment } from './environment.dev-common';

const basePort = '8000';
const baseUrl = `http://localhost:${basePort}/`;

export const environment = {
  ...getCommonEnvironment(baseUrl),
};
