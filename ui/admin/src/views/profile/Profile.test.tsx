import React from 'react';
import { render } from '@testing-library/react';
import { MOCK_AUTHENTICATION } from '../../../tests/utils';
import Profile from './index';

describe('Profile component', () => {
  const renderComponent = () => render(<Profile />);

  it('render basic fields', async () => {
    MOCK_AUTHENTICATION();
    const { queryByText } = renderComponent();
    expect(queryByText('Name')).not.toBeInTheDocument();
    expect(queryByText('email')).not.toBeInTheDocument();
  });
});
