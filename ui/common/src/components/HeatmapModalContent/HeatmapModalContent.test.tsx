import React from 'react';
import { render, screen, waitForElementToBeRemoved, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DEFAULT_SIMULATION_NAME } from '../../types';
import { buildHandler, ENDPOINTS_PATTERN, server } from '../../../tests/utils/server-mocks';
import { heatmaps } from './__fixtures__/heatmaps';
import HeatmapModalContent from '.';

jest.mock('../Heatmap', () => {
  // eslint-disable-next-line
  const React = require('react');

  return () => <div>Heatmap</div>;
});

it('by clicking on Close button calls onClose handler exactly one time', async () => {
  const onClose = jest.fn();

  render(
    <HeatmapModalContent siteId={1} header="Test analysis" onClose={onClose} selectedByDefault={{ dimension: 'any' }} />
  );

  userEvent.click(screen.getByRole('button', { name: /close/i }));

  expect(onClose).toHaveBeenCalledTimes(1);
});

it('by turning labels on, dropdowns will have proper labels', async () => {
  server.use(...[buildHandler(ENDPOINTS_PATTERN.UNIT_HEATMAPS, 'get', heatmaps)]);

  render(
    <HeatmapModalContent
      siteId={1}
      header="Test analysis"
      onClose={jest.fn()}
      selectedByDefault={{ dimension: 'any' }}
      dropdowns={['dimension', 'building', 'floor', 'unit']}
      showDropdownLabel
    />
  );

  const header = screen.getByRole('banner');
  await waitForElementToBeRemoved(within(header).queryByRole('alert'));

  expect(screen.getByText('Insights')).toBeInTheDocument();
  expect(screen.getByText('Building')).toBeInTheDocument();
  expect(screen.getByText('Floor')).toBeInTheDocument();
  expect(screen.getByText('Unit')).toBeInTheDocument();
});

it('by providing selected floor by default, there will be Building and Floor selected properly', async () => {
  render(
    <HeatmapModalContent
      siteId={1}
      header="Test analysis"
      onClose={jest.fn()}
      selectedByDefault={{ dimension: 'any', floor: 12274 }}
    />
  );

  const header = screen.getByRole('banner');
  await waitForElementToBeRemoved(within(header).queryByRole('alert'));

  expect(screen.getByRole('button', { name: /floor 6/i }));
  expect(screen.getByRole('button', { name: /cool man street/i }));
});

it('interacts with default Building and Floor dropdowns correctly', async () => {
  render(
    <HeatmapModalContent
      siteId={1}
      header="Test analysis"
      onClose={jest.fn()}
      selectedByDefault={{ dimension: 'any' }}
    />
  );

  const header = screen.getByRole('banner');
  await waitForElementToBeRemoved(within(header).queryByRole('alert'));

  userEvent.click(screen.getByRole('button', { name: /floor 0/i }));
  userEvent.click(screen.getByRole('option', { name: /floor 1/i }));

  expect(screen.getByRole('button', { name: /floor 1/i })).toBeInTheDocument();

  userEvent.click(screen.getByRole('button', { name: /payso street/i }));
  userEvent.click(screen.getByRole('option', { name: /cool man street/i }));

  expect(screen.getByRole('button', { name: /cool man street/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /floor 5/i })).toBeInTheDocument();
});

it('interacts with Unit dropdown correctly', async () => {
  render(
    <HeatmapModalContent
      siteId={1}
      header="Test analysis"
      onClose={jest.fn()}
      selectedByDefault={{ dimension: 'any' }}
      dropdowns={['building', 'floor', 'unit']}
    />
  );

  const header = screen.getByRole('banner');
  await waitForElementToBeRemoved(within(header).queryByRole('alert'));

  expect(screen.getByRole('button', { name: /all/i })).toBeInTheDocument();

  userEvent.click(screen.getByRole('button', { name: /all/i }));
  userEvent.click(screen.getByRole('option', { name: /worst unit/i }));

  expect(screen.getByRole('button', { name: /worst unit/i })).toBeInTheDocument();

  // if we change Floor value Unit should reset
  userEvent.click(screen.getByRole('button', { name: /floor 0/i }));
  userEvent.click(screen.getByRole('option', { name: /floor 1/i }));

  expect(screen.getByRole('button', { name: /all/i })).toBeInTheDocument();

  // change Unit to see that it will reset later
  userEvent.click(screen.getByRole('button', { name: /all/i }));
  userEvent.click(screen.getByRole('option', { name: /regular unit/i }));

  // if we change Building value Unit should reset
  userEvent.click(screen.getByRole('button', { name: /payso street/i }));
  userEvent.click(screen.getByRole('option', { name: /cool man street/i }));

  expect(screen.getByRole('button', { name: /^all$/i })).toBeInTheDocument();
});

it('interacts with Insights dropdown correctly', async () => {
  server.use(...[buildHandler(ENDPOINTS_PATTERN.UNIT_HEATMAPS, 'get', heatmaps)]);

  render(
    <HeatmapModalContent
      siteId={1}
      header="Test analysis"
      onClose={jest.fn()}
      selectedByDefault={{ dimension: DEFAULT_SIMULATION_NAME }}
      dropdowns={['dimension', 'building', 'floor']}
    />
  );

  const header = screen.getByRole('banner');
  await waitForElementToBeRemoved(within(header).queryByRole('alert'));

  userEvent.click(screen.getByRole('button', { name: /buildings/i }));
  userEvent.click(screen.getByRole('option', { name: /greenary/i }));

  // if we change Building value Dimension should stay
  userEvent.click(screen.getByRole('button', { name: /payso street/i }));
  userEvent.click(screen.getByRole('option', { name: /cool man street/i }));

  await waitForElementToBeRemoved(() => screen.queryByRole('button', { name: 'Loading...' }));
  expect(screen.getByRole('button', { name: /greenary/i })).toBeInTheDocument();

  // if we change Floor value Dimension should stay
  userEvent.click(screen.getByRole('button', { name: /floor 5/i }));
  userEvent.click(screen.getByRole('option', { name: /floor 6/i }));

  await waitForElementToBeRemoved(() => screen.queryByRole('button', { name: 'Loading...' }));
  expect(screen.getByRole('button', { name: /greenary/i })).toBeInTheDocument();
});
