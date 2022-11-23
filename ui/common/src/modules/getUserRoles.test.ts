import cookie from 'js-cookie';
import C from '../constants';
import getUserRoles from './getUserRoles';

beforeEach(() => cookie.remove(C.COOKIES.ROLES));

it('returns an empty array', () => {
  const roles = getUserRoles();

  expect(roles).toEqual([]);
});

it('returns an array with one role', () => {
  const expectedRoles = [C.ROLES.ADMIN];
  cookie.set(C.COOKIES.ROLES, expectedRoles);
  const roles = getUserRoles();

  expect(roles).toEqual(expectedRoles);
});

it('returns an array with many roles', () => {
  const expectedRoles = [C.ROLES.ADMIN, C.ROLES.COMPETITION_VIEWER, C.ROLES.ARCHILYSE_ONE_ADMIN];
  cookie.set(C.COOKIES.ROLES, expectedRoles);
  const roles = getUserRoles();

  expect(roles).toEqual(expectedRoles);
});

it('returns an array with valid roles only', () => {
  cookie.set(C.COOKIES.ROLES, [C.ROLES.ADMIN, 'payaso_role']);
  const roles = getUserRoles();

  expect(roles).toEqual([C.ROLES.ADMIN]);
});
