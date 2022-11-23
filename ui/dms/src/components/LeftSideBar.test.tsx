import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { C } from 'Common';
import { MemoryRouter } from 'react-router-dom';
import { MOCK_AUTHENTICATION } from '../../tests/utils';
import LeftSidebar from './LeftSidebar';

describe('LeftSidebar component', () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="left-sidebar"></div>'; // Needed because <Drawer /> looks for this element programatically
  });

  let props;

  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(
      <MemoryRouter>
        <LeftSidebar {...props} />
      </MemoryRouter>
    );
  };

  beforeEach(() => {
    props = { pathname: C.DMS_VIEWS.BUILDINGS };
  });

  it('Has a settings buttons that navigates to the user profile', async () => {
    renderComponent();
    const settingsAnchorNode = screen.getByRole('link', { name: 'Settings' });
    expect(settingsAnchorNode).toHaveAttribute('href', C.URLS.PROFILE());
  });

  it('Has a logout button that signs out of DMS', async () => {
    renderComponent();
    const logoutAnchorNode = screen.getByRole('link', { name: 'Logout' });
    expect(logoutAnchorNode).toHaveAttribute('href', C.URLS.LOGIN());
  });

  describe('Home button', () => {
    it('Redirects to sites of the client if the user is not admin', async () => {
      MOCK_AUTHENTICATION(C.ROLES.ARCHILYSE_ONE_ADMIN);
      const MOCK_CLIENT_ID = '1'; // Client id  that returns after decoding the token in `MOCK_AUTHENTICATION'

      renderComponent();
      const logoutAnchorNode = screen.getByRole('link', { name: 'Documents' });
      expect(logoutAnchorNode).toHaveAttribute('href', C.URLS.SITES_BY_CLIENT(MOCK_CLIENT_ID));
    });

    it('Redirects to list of clients if we are an admin', async () => {
      MOCK_AUTHENTICATION(C.ROLES.ADMIN);

      renderComponent();
      const logoutAnchorNode = screen.getByRole('link', { name: 'Documents' });
      expect(logoutAnchorNode).toHaveAttribute('href', C.URLS.CLIENTS());
    });
  });
});
