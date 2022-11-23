import React from 'react';
import { Link, NavLink } from 'react-router-dom';
import Icon from '../Icon';
import LogOutButton from './LogOutButton';
import './navbar.scss';

export type NavbarLink = { url: string; label: string };

type Props = {
  links?: NavbarLink[];
  logoRedirect?: string;
};

const Navbar = ({ links = [], logoRedirect }: Props): JSX.Element => {
  const renderLogo = () => {
    if (logoRedirect) {
      return (
        <Link to={logoRedirect}>
          <div id="navbar-logo">
            <Icon>logo</Icon>
          </div>
        </Link>
      );
    }

    return (
      <div id="navbar-logo">
        <Icon>logo</Icon>
      </div>
    );
  };

  return (
    <div className="navbar" role="navigation">
      <LogOutButton />

      {links.map((link, index) => (
        <React.Fragment key={link.url + index}>
          <span>|</span>
          <NavLink to={link.url} activeClassName="current" isActive={(_, location) => location.pathname === link.url}>
            {link.label}
          </NavLink>
        </React.Fragment>
      ))}

      {renderLogo()}
    </div>
  );
};

export default Navbar;
