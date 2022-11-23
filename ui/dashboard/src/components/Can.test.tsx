import React from 'react';
import cookie from 'js-cookie';
import { cleanup, render } from '@testing-library/react';
import { C } from '../common';
import Can from './Can';

afterEach(cleanup);

it("returns null as we didn't pass the yes/no props", () => {
  cookie.set(C.COOKIES.ROLES, [C.ROLES.COMPETITION_ADMIN]);
  const { container } = render(<Can perform="/projects" />);

  expect(container.children.length === 0).toBeTruthy();
});

it('defines role automatically and renders yes() option', () => {
  const expectedText = 'Projects page';
  const unexpectedText = 'Competition page';
  cookie.set(C.COOKIES.ROLES, [C.ROLES.ADMIN]);

  const { queryByText } = render(<Can perform="/projects" yes={() => expectedText} no={() => unexpectedText} />);

  expect(queryByText(unexpectedText)).toBeFalsy();
  expect(queryByText(expectedText)).toBeTruthy();
});

it('defines role automatically and renders no() option', () => {
  const expectedText = 'Projects page';
  const unexpectedText = 'Competition page';
  cookie.set(C.COOKIES.ROLES, [C.ROLES.COMPETITION_ADMIN]);

  const { queryByText } = render(<Can perform="/projects" yes={() => unexpectedText} no={() => expectedText} />);

  expect(queryByText(unexpectedText)).toBeFalsy();
  expect(queryByText(expectedText)).toBeTruthy();
});
