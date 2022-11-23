import React from 'react';
import useSWR from 'swr';
import classNames from 'classnames';
import cookie from 'js-cookie';
import { auth, Icon, ProviderStorage } from 'archilyse-ui-components';
import { Link } from 'react-router-dom';
import { C } from '../common';
import { ProviderRequest } from '../providers';
import { useRouter } from '../common/hooks';
import { getInitialPageUrlByRole } from '../common/modules';
import { checkAccess } from '../common/roles';
import './header.scss';

const SELECTED = 'selected';

const onLogout = history => {
  cookie.remove(C.COOKIES.AUTH_TOKEN);
  cookie.remove(C.COOKIES.ROLES);
  ProviderStorage.clear();
  history.push(C.URLS.LOGIN());
};

const getLinkClass = (href, pathname) => classNames({ [SELECTED]: href === pathname });

const getUserInfoUrl = (userRoles: string[]) => {
  const { id } = auth.getUserInfo();
  return checkAccess('/profile') ? C.ENDPOINTS.USER(id) : null;
};

const Header = props => {
  const userRoles = auth.getRoles();

  const adminLinks = [
    ...(checkAccess('/clients') ? [{ href: '/clients', label: 'Clients' }] : []),
    ...(checkAccess('/users') ? [{ href: '/users', label: 'Users' }] : []),
  ];

  const { history, pathname } = useRouter();
  const { data: user } = useSWR(getUserInfoUrl(userRoles), ProviderRequest.get);
  if (!userRoles || !userRoles.length) return null;

  return (
    <div id="admin-header" className="header">
      <div className="admin-navbar">
        {adminLinks.map(({ href, label }) => (
          <Link className={getLinkClass(href, pathname)} key={label} to={href}>
            {label}
          </Link>
        ))}
      </div>
      <div className="dms-navbar">
        {user && (
          <>
            <Link to={C.URLS.PROFILE()}>
              <small>{user.login}</small>
            </Link>
            <small>|</small>
          </>
        )}
        <div className="logout" onClick={() => onLogout(history)}>
          <small>Log out</small>
        </div>
        <small>|</small>
        <Link to={C.URLS.CLIENTS()}>
          <small>{'Admin'}</small>
        </Link>

        <Link to={getInitialPageUrlByRole()} className="navbar-logo">
          <Icon>logo</Icon>
        </Link>
      </div>
    </div>
  );
};

export default Header;
