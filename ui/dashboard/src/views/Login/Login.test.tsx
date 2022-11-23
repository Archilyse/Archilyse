import * as React from 'react';
import { cleanup, render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from './Login';

afterEach(cleanup);

it('renders correctly', () => {
  const { container } = render(
    <BrowserRouter>
      <Login />
    </BrowserRouter>
  );
  expect(container).toMatchSnapshot();
});
