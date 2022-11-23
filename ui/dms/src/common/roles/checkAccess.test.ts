import cookie from 'js-cookie';
import { MOCK_AUTHENTICATION } from '../../../tests/utils';
import C from '../constants';
import { ActionsType, checkAccess } from '.';

beforeEach(() => cookie.remove(C.COOKIES.AUTH_TOKEN));

it('should be falsy if the user has no roles', () => {
  const mockAction: ActionsType = '/clients';
  const can = checkAccess(mockAction);
  expect(can).toBeFalsy();
});

it('should take user role automatically and check access to be true', () => {
  MOCK_AUTHENTICATION(C.ROLES.ARCHILYSE_ONE_ADMIN);

  const mockAction: ActionsType = '/sites';
  const can = checkAccess(mockAction);
  expect(can).toBeTruthy();
});
it('should not allow DMS Admin to access clients', () => {
  MOCK_AUTHENTICATION(C.ROLES.ARCHILYSE_ONE_ADMIN);

  const mockAction: ActionsType = '/clients';
  const can = checkAccess(mockAction);
  expect(can).toBeFalsy();
});

it('should check array of actions', () => {
  MOCK_AUTHENTICATION();

  const mockActions: any[] = ['/users', '/sites'];
  const can = checkAccess(mockActions);
  expect(can).toBeTruthy();
});
