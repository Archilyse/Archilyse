import React from 'react';
import { render } from '@testing-library/react';
import { MemoryRouter, Route } from 'react-router-dom';
import { C } from '../../src/common';

export const renderWithRouter = (ui, route: string) => {
  const paths = [C.URLS.COMPETITION(':id'), C.URLS.QA(':siteId')];

  return render(
    <MemoryRouter initialEntries={[route]}>
      <Route path={paths} exact>
        {ui}
      </Route>
    </MemoryRouter>
  );
};
