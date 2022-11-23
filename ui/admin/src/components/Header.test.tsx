import * as React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { cleanup, render, screen } from '@testing-library/react';
import { C } from 'Common';
import { MOCK_AUTHENTICATION } from '../../tests/utils';
import Header from '../../src/components/Header';

afterEach(cleanup);

jest.mock('jwt-decode', () => () => ({
  sub: {
    id: 1,
  },
}));

describe('In the Admin', () => {
  it('An admin can see regular links go to the DMS', async () => {
    MOCK_AUTHENTICATION(C.ROLES.ADMIN);

    render(
      <MemoryRouter initialEntries={['/clients']}>
        <Header />
      </MemoryRouter>
    );

    expect(screen.getByRole('link', { name: 'Clients' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Users' })).toBeInTheDocument();
  });
});
