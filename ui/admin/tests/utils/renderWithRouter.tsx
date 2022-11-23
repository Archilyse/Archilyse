import React from 'react';
import { render } from '@testing-library/react';
import { MemoryRouter, Route } from 'react-router-dom';
import { C } from 'Common';

const { PIPELINE, ...restUrls } = C.URLS;
const renderWithRouter = (ui, route: string) => {
  const paths = Object.values(restUrls).map(urlHelper => {
    if (typeof urlHelper === 'string') return urlHelper;
    const mockParam = '1';
    return urlHelper(mockParam);
  });

  return render(
    <MemoryRouter initialEntries={[route]}>
      <Route path={paths} exact>
        {ui}
      </Route>
    </MemoryRouter>
  );
};

export default renderWithRouter;
