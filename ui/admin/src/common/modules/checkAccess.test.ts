import cookie from 'js-cookie';
import { ActionsType, checkAccess } from '../roles';
import { MOCK_AUTHENTICATION } from '../../../tests/utils';
import C from '../constants';

beforeEach(() => cookie.remove(C.COOKIES.AUTH_TOKEN));

it('should be falsy if the user has no roles', () => {
  const mockAction: ActionsType = '/clients';
  const can = checkAccess(mockAction);
  expect(can).toBeFalsy();
});

it('should take user role automatically and check access to be true', () => {
  MOCK_AUTHENTICATION(C.ROLES.TEAMMEMBER);

  const mockAction: ActionsType = '/clients';
  const can = checkAccess(mockAction);
  expect(can).toBeTruthy();
});

it('should check array of actions', () => {
  MOCK_AUTHENTICATION();

  const mockActions: ActionsType[] = ['/users', '/sites'];
  const can = checkAccess(mockActions);
  expect(can).toBeTruthy();
});
