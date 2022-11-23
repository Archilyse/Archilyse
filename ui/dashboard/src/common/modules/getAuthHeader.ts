import cookie from 'js-cookie';
import C from '../constants';

export default () => {
  const accessToken = cookie.get(C.COOKIES.AUTH_TOKEN);
  return { Authorization: `Bearer ${accessToken}` };
};
