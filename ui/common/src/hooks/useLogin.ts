import { useContext } from 'react';
import { useHistory } from 'react-router';
import { SnackbarContext } from '../components';
import C from '../constants';
import { auth } from '../modules';
import { ProviderRequest } from '../providers';

type Props = {
  getInitialPageUrl: () => string;
  checkAccess: (intent: string) => boolean;
};

const NOT_AUTHORIZED = 401;
const LOGIN_WAIT_TIME = 1000;

const useLogin = ({ getInitialPageUrl, checkAccess }: Props) => {
  const history = useHistory<{ from: Location }>();

  const snackbar = useContext(SnackbarContext);

  const _redirect = () => {
    const state = history.location.state;

    if (state?.from && state.from.pathname !== '/') {
      const { from } = state;
      history.push(from.pathname + from.search);
    } else {
      history.push(getInitialPageUrl());
    }
  };

  const extractPathnameFromUrl = (url: string) => {
    const qsStart = url.indexOf('?');

    if (qsStart > -1) {
      return url.substr(0, qsStart);
    }

    return url;
  };

  const handleSubmit = async value => {
    try {
      const response = await ProviderRequest.post(C.ENDPOINTS.AUTHENTICATE(), value);
      auth.authenticate(response.access_token, response.roles);

      const intentUrl = extractPathnameFromUrl(getInitialPageUrl());
      const isAllowedToLogin = checkAccess(intentUrl);

      if (!isAllowedToLogin) {
        auth.deauthenticate();
        snackbar.show({ message: 'Insufficient permissions to access this application', severity: 'error' });
      } else {
        snackbar.show({ message: 'Logged successfully', severity: 'success' });
        setTimeout(_redirect, LOGIN_WAIT_TIME);
      }
    } catch (error) {
      let message;
      if (error?.response.status === NOT_AUTHORIZED) {
        message = 'User or password invalid, please try again';
      } else {
        message = 'Error trying to log in, please try again or contact support';
      }
      snackbar.show({ message, severity: 'error' });
    }
  };

  return { handleSubmit };
};

export default useLogin;
