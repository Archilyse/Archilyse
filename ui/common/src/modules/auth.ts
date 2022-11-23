import cookie from 'js-cookie';
import jwt_decode from 'jwt-decode';
import C from '../constants';

const EXPIRATION_DAYS = 7;
type IdentityType = {
  id: number;
  client_id: number;
  group_id: number;
  name: string;
};
export const authenticate = (access_token, roles) => {
  cookie.set(C.COOKIES.AUTH_TOKEN, access_token, { expires: EXPIRATION_DAYS });
  cookie.set(C.COOKIES.ROLES, roles, { expires: EXPIRATION_DAYS });
};

export const deauthenticate = () => {
  cookie.remove(C.COOKIES.AUTH_TOKEN);
  cookie.remove(C.COOKIES.ROLES);
};

export const isAuthenticated = () => {
  const accessToken = cookie.get(C.COOKIES.AUTH_TOKEN);
  return Boolean(accessToken);
};

export const getRoles = () => {
  const roles: string = cookie.get('roles');
  return roles?.split(',').map(role => role.replace('[', '').replace(']', '').replace(/"/g, ''));
};

export const getUserInfo = (): IdentityType => {
  const accessToken = cookie.get(C.COOKIES.AUTH_TOKEN);
  const decodedToken = jwt_decode(accessToken);
  return decodedToken && decodedToken.sub;
};

export const hasValidRole = validRoles => {
  const userRoles = getRoles();
  return validRoles.some(validRole => userRoles.includes(validRole));
};
