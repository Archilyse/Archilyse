import React from 'react';
import { screen, waitForElementToBeRemoved } from '@testing-library/react';
import { C } from 'Common';
import { buildHandler, ENDPOINTS_PATTERN, server } from '../../../tests/server-mocks';
import { renderWithRouter } from '../../../tests/renderWithRouter';
import { simulationWithError } from './__fixtures__/simulation';
import Simulation from '.';

it.each([
  [403, { msg: 'Forbidden! Payaso can not request simulation' }, /forbidden!/i],
  [200, simulationWithError, simulationWithError.result.msg],
])('shows error message if server returned error with status %i', async (status, result, expectedMessage) => {
  server.use(...[buildHandler(ENDPOINTS_PATTERN.SIMULATION, 'get', result, status)]);

  renderWithRouter(<Simulation />, C.URLS.SIMULATION_VIEW(1));

  await waitForElementToBeRemoved(screen.getByRole('alert'));

  expect(screen.getByText(expectedMessage)).toBeInTheDocument();
});
