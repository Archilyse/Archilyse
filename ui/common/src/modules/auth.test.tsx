import cookie from 'js-cookie';
import C from '../constants';
import MOCK_AUTHENTICATION from '../../tests/utils/mockAuthentication';
import * as auth from './auth';

beforeEach(() => cookie.remove(C.COOKIES.AUTH_TOKEN));

it('sets the authorization header if access token is provided', () => {
  MOCK_AUTHENTICATION();

  const authCookie = cookie.get(C.COOKIES.AUTH_TOKEN);
  expect(authCookie).toBeTruthy();
  expect(auth.isAuthenticated()).toEqual(true);

  expect(auth.getRoles().includes(C.ROLES.ADMIN)).toEqual(true);
});

it('To show that the user is not authenticated by default', () => {
  expect(auth.isAuthenticated()).toEqual(false);
});

it('To check if the user has valid roles with no values', () => {
  MOCK_AUTHENTICATION([C.ROLES.DMS_LIMITED]);
  expect(auth.hasValidRole([])).toEqual(false);
});

it('To check if the user has valid roles with the right configuration of 1 role', () => {
  MOCK_AUTHENTICATION([C.ROLES.DMS_LIMITED]);
  expect(auth.hasValidRole([C.ROLES.DMS_LIMITED])).toEqual(true);
});

it('To check if the user has valid roles with multiple valid roles', () => {
  MOCK_AUTHENTICATION([C.ROLES.DMS_LIMITED, C.ROLES.ADMIN]);
  expect(auth.hasValidRole([C.ROLES.DMS_LIMITED, C.ROLES.ADMIN])).toEqual(true);
});

it('To check if the user has valid roles with multiple invalid roles', () => {
  MOCK_AUTHENTICATION([C.ROLES.ADMIN, C.ROLES.ARCHILYSE_ONE_ADMIN]);
  expect(auth.hasValidRole([C.ROLES.DMS_LIMITED])).toEqual(false);
});
