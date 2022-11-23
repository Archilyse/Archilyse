import React from 'react';
import cookie from 'js-cookie';
import { Link } from 'react-router-dom';
import C from '../../constants';
import { ProviderStorage } from '../../providers';

const LogOutButton = (): JSX.Element => {
  const handleLogOut = () => {
    cookie.remove(C.COOKIES.AUTH_TOKEN);
    cookie.remove(C.COOKIES.ROLES);

    ProviderStorage.clear();
  };

  return (
    <Link onClick={handleLogOut} to={C.LOGIN()}>
      Log out
    </Link>
  );
};

export default LogOutButton;
