import React from 'react';
import { screen, waitForElementToBeRemoved, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithRouter } from '../../../tests/utils/renderWithRouter';
import { C } from '../../common';
import { buildHandler, ENDPOINTS_PATTERN, server } from '../../../tests/utils/server-mocks';
import QA from './QA';
import { site } from './__fixtures__/site';
import { units } from './__fixtures__/units';
import { siteStructure } from './__fixtures__/siteStructure';
import { simulationValidation } from './__fixtures__/simulationValidaton';
import { heatmaps } from './__fixtures__/heatmaps';

const SPINNER_TIMEOUT_MS = 3000;

jest.mock('archilyse-ui-components', () => {
  // eslint-disable-next-line
  const React = require('react');

  return {
    // @ts-ignore
    ...jest.requireActual('archilyse-ui-components'),
    Heatmap: () => <div>Heatmap</div>,
    SimulationViewer: () => <div />,
  };
});

const waitForLoadingSpinnerToDisappear = async () => {
  await waitForElementToBeRemoved(within(screen.getByRole('main')).queryByRole('alert'), {
    timeout: SPINNER_TIMEOUT_MS,
  });
};
const selectInDropdown = async (dropdownValue: string | RegExp, valueToSelect: string | RegExp) => {
  const drawer = within(screen.getByRole('complementary'));

  userEvent.click(drawer.getByText(dropdownValue));
  userEvent.click(screen.getByRole('option', { name: valueToSelect }));
  await waitForLoadingSpinnerToDisappear();
};

it('checks the Single/Group toggles works as expected', async () => {
  server.use(
    ...[
      buildHandler(ENDPOINTS_PATTERN.SITE, 'get', site),
      buildHandler(ENDPOINTS_PATTERN.SITE_UNITS, 'get', units),
      buildHandler(ENDPOINTS_PATTERN.SITE_STRUCTURE, 'get', siteStructure),
      buildHandler(ENDPOINTS_PATTERN.UNIT_HEATMAPS, 'get', heatmaps),
    ]
  );

  renderWithRouter(<QA />, C.URLS.QA(1));

  await waitForLoadingSpinnerToDisappear();

  expect(screen.getByText(/floor 0 - buildings/i)).toBeInTheDocument();
  expect(screen.getByText(/floor 0 - greenary/i)).toBeInTheDocument();

  userEvent.click(screen.getByText('Single'));
  await waitForLoadingSpinnerToDisappear();

  expect(screen.getByText(/floor 0 - buildings/i)).toBeInTheDocument();
  expect(screen.queryByText(/floor 0 - greenary/i)).not.toBeInTheDocument();

  userEvent.click(screen.getByText('Group'));
  await waitForLoadingSpinnerToDisappear();
});

it('checks the dropdowns works as expected', async () => {
  server.use(
    ...[
      buildHandler(ENDPOINTS_PATTERN.SITE, 'get', site),
      buildHandler(ENDPOINTS_PATTERN.SITE_UNITS, 'get', units),
      buildHandler(ENDPOINTS_PATTERN.SITE_STRUCTURE, 'get', siteStructure),
      buildHandler(ENDPOINTS_PATTERN.UNIT_HEATMAPS, 'get', heatmaps),
    ]
  );

  renderWithRouter(<QA />, C.URLS.QA(1));

  const mainContent = within(screen.getByRole('main'));

  await waitForLoadingSpinnerToDisappear();

  expect(mainContent.getByText(/floor 0 - buildings/i)).toBeInTheDocument();
  expect(mainContent.getByText(/floor 0 - greenary/i)).toBeInTheDocument();

  // check Simulation Type dropdown
  await selectInDropdown(/view/i, /sun/i);

  expect(mainContent.queryByText(/floor 0 - buildings/i)).not.toBeInTheDocument();
  expect(mainContent.queryByText(/floor 0 - greenary/i)).not.toBeInTheDocument();
  expect(mainContent.getByText(/floor 0 - sun-2018-03-21/i)).toBeInTheDocument();

  await selectInDropdown(/sun/i, /connectivity/i);

  expect(mainContent.queryByText(/floor 0 - sun-2018-03-21/i)).not.toBeInTheDocument();
  expect(mainContent.getByText(/floor 0 - connectivity_KITCHEN_distance/i)).toBeInTheDocument();

  await selectInDropdown(/connectivity/i, /view/i);

  // check Building dropdown
  await selectInDropdown(/payso street, big/i, /cool man street, small/i);

  expect(mainContent.queryByText(/floor 0/i)).not.toBeInTheDocument();
  expect(mainContent.getByText(/floor 5 - buildings/i)).toBeInTheDocument();
  expect(mainContent.getByText(/floor 5 - greenary/i)).toBeInTheDocument();

  // check Floor dropdown
  await selectInDropdown(/floor 5/i, /floor 6/i);

  expect(mainContent.queryByText(/floor 5 - buildings/i)).not.toBeInTheDocument();
  expect(mainContent.queryByText(/floor 5 - greenary/i)).not.toBeInTheDocument();
  expect(mainContent.getByText(/floor 6 - buildings/i)).toBeInTheDocument();
  expect(mainContent.getByText(/floor 6 - greenary/i)).toBeInTheDocument();

  // check Unit dropdown
  await selectInDropdown(/unit/i, /coolest unit/i);

  expect(mainContent.queryByText(/floor 6 - buildings/i)).not.toBeInTheDocument();
  expect(mainContent.queryByText(/floor 6 - greenary/i)).not.toBeInTheDocument();
  expect(mainContent.getByText(/unit coolest unit - buildings/i)).toBeInTheDocument();
  expect(mainContent.getByText(/unit coolest unit - greenary/i)).toBeInTheDocument();
});

it('checks the Validation Dialog interaction works as expected', async () => {
  server.use(
    ...[
      buildHandler(ENDPOINTS_PATTERN.SITE, 'get', site),
      buildHandler(ENDPOINTS_PATTERN.SITE_UNITS, 'get', units),
      buildHandler(ENDPOINTS_PATTERN.SITE_STRUCTURE, 'get', siteStructure),
      buildHandler(ENDPOINTS_PATTERN.SITE_SIM_VALIDATION, 'get', simulationValidation),

      buildHandler(ENDPOINTS_PATTERN.UNIT_HEATMAPS, 'get', heatmaps),
    ]
  );

  renderWithRouter(<QA />, C.URLS.QA(1));

  const mainContent = within(screen.getByRole('main'));
  const drawer = within(screen.getByRole('complementary'));

  await waitForLoadingSpinnerToDisappear();

  expect(mainContent.getByText(/floor 0 - buildings/i)).toBeInTheDocument();
  expect(mainContent.getByText(/floor 0 - greenary/i)).toBeInTheDocument();

  userEvent.click(drawer.getByText(/coolest unit/i));
  await waitForLoadingSpinnerToDisappear();

  expect(mainContent.queryByText(/floor 6 - buildings/i)).not.toBeInTheDocument();
  expect(mainContent.queryByText(/floor 6 - greenary/i)).not.toBeInTheDocument();
  expect(mainContent.getByText(/unit coolest unit - buildings/i)).toBeInTheDocument();
  expect(mainContent.getByText(/unit coolest unit - greenary/i)).toBeInTheDocument();
});
