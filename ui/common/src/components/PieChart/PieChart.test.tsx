import * as React from 'react';
import { cleanup, render, waitFor } from '@testing-library/react';
import PieChart from './index';

afterEach(cleanup);

const MOCK_DATA = [
  { x: 'HNF', y: 50 },
  { x: 'ANF', y: 20 },
  { x: 'NNF', y: 10 },
  { x: 'FF', y: 10 },
  { x: 'VF', y: 10 },
];

const MOCK_DATA_2 = [
  { x: 'HNF', y: 50.452342423432423 },
  { x: 'ANF', y: 20 },
  { x: 'NNF', y: 10 },
  { x: 'FF', y: 10 },
  { x: 'VF', y: 10 },
];

const MOCK_COLORS = ['red', 'green', 'blue', 'yellow'];
it('renders correctly', () => {
  const { container } = render(
    <PieChart data={MOCK_DATA} showLabelByDefault={true} colorFunction={({ datum }) => MOCK_COLORS[datum._x]} />
  );
  expect(container).toMatchSnapshot();
});

it('renders correctly an y value with a lot of decimals', async () => {
  const EXPECTED_INITIAL_LABEL = new RegExp('50.5%');

  const { queryByText, getByText } = render(
    <PieChart data={MOCK_DATA_2} showLabelByDefault={true} colorFunction={({ datum }) => MOCK_COLORS[datum._x]} />
  );

  const isComponentLoaded = () => queryByText(EXPECTED_INITIAL_LABEL);
  await waitFor(() => expect(isComponentLoaded()).toBeTruthy());

  expect(getByText(EXPECTED_INITIAL_LABEL)).toBeTruthy();
});
