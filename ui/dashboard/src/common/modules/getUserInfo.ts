import cookie from 'js-cookie';
import jwt_decode from 'jwt-decode';
import C from '../constants';

type IdentityType = {
  id: number;
  client_id: number;
  group_id: number;
  name: string;
};
export default (): IdentityType => {
  const accessToken = cookie.get(C.COOKIES.AUTH_TOKEN);
  const decodedToken = jwt_decode(accessToken);
  return decodedToken && decodedToken.identity;
};
