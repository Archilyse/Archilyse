import cookie from 'js-cookie';
import C from '../constants';

export default (): string[] => {
  const rolesFromCookie: string = cookie.get(C.COOKIES.ROLES);

  try {
    const roles: string[] = JSON.parse(rolesFromCookie);

    return roles.filter(role => C.ROLES[role.toUpperCase()]);
  } catch (error) {
    console.error('Error while trying to parse cookie', error);
    return [];
  }
};
