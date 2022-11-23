import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { BiLogOut } from 'react-icons/bi';
import { Redirect } from 'react-router-dom';
import { useHistory } from 'react-router';
import cookie from 'js-cookie';
import { ProviderStorage } from 'archilyse-ui-components';
import AppContext from '../../AppContext';
import ToolbarButton from '../toolbar-button/export';
import { COOKIES } from '../../constants';

const HR_STYLE = {
  width: '100%',
  marginBottom: '15px',
};

export default function ToolbarLogoutButton() {
  const history = useHistory();
  const [isLoggedIn, setIsLoggedIn] = useState(true);

  const logOut = async event => {
    cookie.remove(COOKIES.AUTH_TOKEN);
    cookie.remove(COOKIES.ROLES);
    ProviderStorage.clear();
    setIsLoggedIn(false);
  };

  if (isLoggedIn) {
    return (
      <>
        <hr style={HR_STYLE} />
        <ToolbarButton
          id="logout-button"
          data-testid="logout-button"
          active={false}
          tooltip={'Log out from the Editor'}
          onClick={logOut}
        >
          <BiLogOut />
        </ToolbarButton>
      </>
    );
  }
  return <Redirect to={{ pathname: history.location.pathname }} />;
}

ToolbarLogoutButton.propTypes = {};
