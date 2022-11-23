import cookie from 'js-cookie';
import { ActionsType, checkAccess } from '../roles';
import C from '../constants';
import actions from './actions';

beforeEach(() => cookie.remove(C.COOKIES.ROLES));

it('should be falsy if the user has no roles', () => {
  const mockAction: ActionsType[] = [...actions];
  const can = checkAccess(mockAction);
  expect(can).toBeFalsy();
});

it('should check Admin can access everything', () => {
  cookie.set(C.COOKIES.ROLES, [C.ROLES.ADMIN]);

  const mockAction: ActionsType[] = [...actions];
  const can = checkAccess(mockAction);
  expect(can).toBeTruthy();
});

it('should check access for user with one role', () => {
  cookie.set(C.COOKIES.ROLES, [C.ROLES.COMPETITION_ADMIN]);

  const mockAction: ActionsType = '/competition/:id';
  const can = checkAccess(mockAction);
  expect(can).toBeTruthy();
});

it('should check access for user with two roles', () => {
  cookie.set(C.COOKIES.ROLES, [C.ROLES.COMPETITION_VIEWER, C.ROLES.COMPETITION_ADMIN]);

  const mockAction: ActionsType[] = ['/competition/:id'];
  const can = checkAccess(mockAction);
  expect(can).toBeTruthy();
});
