import React from 'react';
import { fireEvent, render, screen, waitForElementToBeRemoved, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { buildHandler, ENDPOINTS_PATTERN, server } from '../../../../../tests/utils/server-mocks';
import flatDeviationConfiguration from '../../__fixtures__/flatDeviationConfiguration';
import { FlatDeviationResponseType } from '../../../../common/types';
import FlatDeviationModalContent from './FlatDeviationModalContent';

const GHOST_ROW = 1;

it('if change apartment-type ghost row it will be saved and new row appears', async () => {
  const onClose = jest.fn();
  const expected = '6.5';
  const expectedRows = GHOST_ROW + 1;

  render(<FlatDeviationModalContent onClose={onClose} />);

  const tbodyElement = screen.getAllByRole('rowgroup')[1];
  await waitForElementToBeRemoved(() => within(tbodyElement).getByRole('alert'));

  userEvent.click(screen.getByRole('button', { name: 'apartment-type-ghost' }));
  fireEvent.change(screen.getByRole('spinbutton'), { target: { value: expected } });

  // clicks outside
  userEvent.click(screen.getByRole('heading'));

  expect(screen.getByRole('button', { name: 'apartment-type-real' }).textContent).toBe(expected);
  expect(within(tbodyElement).getAllByRole('row').length).toBe(expectedRows);

  expect(onClose).toHaveBeenCalledTimes(0);
});

it('if change percentage ghost row it will be saved and new row appears', async () => {
  const onClose = jest.fn();
  const entered = '50';
  const expected = `${entered}%`;
  const expectedRows = GHOST_ROW + 1;

  render(<FlatDeviationModalContent onClose={onClose} />);

  const tbodyElement = screen.getAllByRole('rowgroup')[1];
  await waitForElementToBeRemoved(() => within(tbodyElement).getByRole('alert'));

  userEvent.click(screen.getByRole('button', { name: 'percentage-ghost' }));
  fireEvent.change(screen.getByRole('spinbutton'), { target: { value: entered } });

  // clicks outside
  userEvent.click(screen.getByRole('heading'));

  expect(screen.getByRole('button', { name: 'percentage-real' }).textContent).toBe(expected);

  expect(within(tbodyElement).getAllByRole('row').length).toBe(expectedRows);

  expect(onClose).toHaveBeenCalledTimes(0);
});

it('can add new rows via "+" button icon', async () => {
  const onClose = jest.fn();
  const expectedRows = GHOST_ROW + 4;

  render(<FlatDeviationModalContent onClose={onClose} />);

  const tbodyElement = screen.getAllByRole('rowgroup')[1];
  await waitForElementToBeRemoved(() => within(tbodyElement).getByRole('alert'));

  userEvent.click(screen.getByRole('button', { name: 'add' }));
  userEvent.click(screen.getByRole('button', { name: 'add' }));
  userEvent.click(screen.getByRole('button', { name: 'add' }));
  userEvent.click(screen.getByRole('button', { name: 'add' }));

  expect(within(tbodyElement).getAllByRole('row').length).toBe(expectedRows);

  expect(onClose).toHaveBeenCalledTimes(0);
});

it('can remove rows via "X" button icon', async () => {
  const onClose = jest.fn();
  const expectedRows = GHOST_ROW;

  server.use(
    buildHandler(ENDPOINTS_PATTERN.COMPETITION_PARAMETERS, 'get', {
      flat_types_distribution: flatDeviationConfiguration,
    })
  );

  render(<FlatDeviationModalContent onClose={onClose} />);

  const tbodyElement = screen.getAllByRole('rowgroup')[1];
  await waitForElementToBeRemoved(() => within(tbodyElement).getByRole('alert'));

  flatDeviationConfiguration.forEach(() => {
    userEvent.click(screen.getAllByRole('button', { name: 'remove' })[0]);
  });

  expect(within(tbodyElement).getAllByRole('row').length).toBe(expectedRows);

  expect(onClose).toHaveBeenCalledTimes(0);
});

it('can edit existing rows', async () => {
  const onClose = jest.fn();
  const expectedRows = GHOST_ROW + flatDeviationConfiguration.length;
  const expectedValues: FlatDeviationResponseType[] = [
    { apartment_type: 2.5, percentage: 35 },
    { apartment_type: 4.5, percentage: 20 },
    { apartment_type: 6, percentage: 45 },
  ];
  const updatedValues = expectedValues.map(value => ({ ...value, percentage: value.percentage / 100 }));

  server.use(
    ...[
      buildHandler(ENDPOINTS_PATTERN.COMPETITION_PARAMETERS, 'get', {
        flat_types_distribution: flatDeviationConfiguration,
      }),
      buildHandler(ENDPOINTS_PATTERN.COMPETITION_PARAMETERS, 'put', {
        flat_types_distribution: updatedValues,
      }),
    ]
  );

  render(<FlatDeviationModalContent onClose={onClose} />);

  const tbodyElement = screen.getAllByRole('rowgroup')[1];
  await waitForElementToBeRemoved(() => within(tbodyElement).getByRole('alert'));

  flatDeviationConfiguration.forEach((_, index) => {
    userEvent.click(screen.getAllByRole('button', { name: 'apartment-type-real' })[index]);
    fireEvent.change(screen.getByRole('spinbutton'), { target: { value: expectedValues[index].apartment_type } });
    userEvent.click(screen.getAllByRole('button', { name: 'percentage-real' })[index]);
    fireEvent.change(screen.getByRole('spinbutton'), { target: { value: expectedValues[index].percentage } });
  });

  const submitButton = screen.getByText(/apply/i);
  userEvent.click(submitButton);
  await waitForElementToBeRemoved(() => within(submitButton).getByRole('alert'));

  expectedValues.forEach((expected, index) => {
    const apartmentCell = screen.getAllByRole('button', { name: 'apartment-type-real' })[index];
    const percentageCell = screen.getAllByRole('button', { name: 'percentage-real' })[index];

    expect(apartmentCell).toHaveTextContent(String(expected.apartment_type));
    expect(percentageCell).toHaveTextContent(`${expected.percentage}%`);
  });

  expect(within(tbodyElement).getAllByRole('row').length).toBe(expectedRows);

  expect(onClose).toHaveBeenCalledTimes(0);
});
