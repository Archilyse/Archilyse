import React from 'react';
import { render } from '@testing-library/react';
import { MemoryRouter, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { ReactPlanner } from '../export'; //react-planner

export default (props, store) => {
  return render(
    <Provider store={store}>
      <MemoryRouter initialEntries={['/1']}>
        <Route path="/:id">
          <ReactPlanner {...props} />
        </Route>
      </MemoryRouter>
    </Provider>
  );
};
