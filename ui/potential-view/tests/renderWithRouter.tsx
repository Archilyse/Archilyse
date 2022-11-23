import React from 'react';
import { render } from '@testing-library/react';
import { MemoryRouter, Route } from 'react-router-dom';
import { C } from 'Common';

export const renderWithRouter = (ui, route: string) => {
  const paths = [C.URLS.SIMULATION_VIEW(':id')];

  return render(
    <MemoryRouter initialEntries={[route]}>
      <Route path={paths}>{ui}</Route>
    </MemoryRouter>
  );
};
