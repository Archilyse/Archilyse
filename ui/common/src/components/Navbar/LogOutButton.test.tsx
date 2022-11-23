import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import cookie from 'js-cookie';
import { MemoryRouter } from 'react-router-dom';
import C from '../../constants';
import MOCK_AUTHENTICATION from '../../../tests/utils/mockAuthentication';
import LogOutButton from './LogOutButton';

beforeAll(() => MOCK_AUTHENTICATION());

it('if clicks on log out cookie should be cleared', () => {
  render(
    <MemoryRouter initialEntries={['/projects']}>
      <LogOutButton />
    </MemoryRouter>
  );

  expect(cookie.get(C.COOKIES.AUTH_TOKEN)).not.toBe(undefined);
  expect(cookie.get(C.COOKIES.ROLES)).not.toBe(undefined);

  userEvent.click(screen.getByText(/log out/i));

  expect(cookie.get(C.COOKIES.AUTH_TOKEN)).toBe(undefined);
  expect(cookie.get(C.COOKIES.ROLES)).toBe(undefined);
});
