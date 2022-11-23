import cookie from 'js-cookie';
import { C } from '../../src/common';

const mockToken =
  'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTYyNTUyOTYwMCwianRpIjoiNjViNjU5ZWQtYjA5Ni00ZGRjLWI3NDUtMTc2MDYxYWQ5YmFlIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJpZCI6MSwibmFtZSI6ImFkbWluIiwiZ3JvdXBfaWQiOjEsImNsaWVudF9pZCI6bnVsbH0sIm5iZiI6MTYyNTUyOTYwMCwiZXhwIjoxNjI2ODI1NjAwfQ.mPq204JFRVCi-8vPCDqwQcGngu731N16rDp3wIOr5go';

const MOCK_AUTHENTICATION = (role: typeof C.ROLES[keyof typeof C.ROLES] = 'ADMIN'): void => {
  cookie.set(C.COOKIES.AUTH_TOKEN, mockToken);
  cookie.set(C.COOKIES.ROLES, [role]);
};

export default MOCK_AUTHENTICATION;
