import React from 'react';
import { render } from '@testing-library/react';
import { C } from 'Common';
import { MOCK_AUTHENTICATION } from '../../../tests/utils';
import Profile from './index';

const mockPathname = '/profile';
jest.mock('../../common/hooks', () => ({
  useRouter: () => ({ pathname: mockPathname }),
}));

describe('Profile component', () => {
  const renderComponent = () => render(<Profile />);

  it('renders "create user" and "permissions" when the user has dms admin role', async () => {
    MOCK_AUTHENTICATION(C.ROLES.ARCHILYSE_ONE_ADMIN);
    const { queryByText } = renderComponent();
    expect(queryByText('Create user')).toBeInTheDocument();
    expect(queryByText('User management')).toBeInTheDocument();
  });
  it('does not render "create user" and "permissions" when the user has not dms admin role', async () => {
    MOCK_AUTHENTICATION(C.ROLES.DMS_LIMITED);
    const { queryByText } = renderComponent();
    expect(queryByText('Create user')).not.toBeInTheDocument();
    expect(queryByText('User management')).not.toBeInTheDocument();
  });
});
