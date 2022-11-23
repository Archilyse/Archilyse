import * as React from 'react';
import { cleanup, render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Breadcrumb } from '.';

afterEach(cleanup);

const MOCK_HIERARCHY = [
  { text: 'All Clients', href: '/some-url-1' },
  { text: 'Client name', href: '/some-url-2' },
  { text: 'Site: some words here', href: '/some-url-3' },
  { text: 'Building: 23241234', href: '/some-url-4' },
  { text: 'Folder - 1', href: '/some-url-5' },
];

it('renders correctly empty breadcrumb', () => {
  const { container } = render(
    <MemoryRouter>
      <Breadcrumb />
    </MemoryRouter>
  );

  expect(container).toMatchSnapshot();
});

it('renders correctly breadcrumb with hierarchy', () => {
  const { container } = render(
    <MemoryRouter>
      <Breadcrumb hierarchy={MOCK_HIERARCHY} />
    </MemoryRouter>
  );

  expect(container).toMatchSnapshot();
});
