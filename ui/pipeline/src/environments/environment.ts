import { getCommonEnvironment } from './environment.dev-common';

const baseUrl = `http://localhost/api/`;

export const environment = {
  ...getCommonEnvironment(baseUrl),
};
