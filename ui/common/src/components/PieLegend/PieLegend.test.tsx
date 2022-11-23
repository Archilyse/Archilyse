import * as React from 'react';
import { cleanup, render } from '@testing-library/react';
import PieLegend from './index';

afterEach(cleanup);

const MOCK_DATA = ['HNF', 'NNF', 'ANF', 'FF', 'VF'];

const MOCK_ANALYSIS_COLORS = {
  HNF: '#00B34A',
  ANF: '#FF3C2E',
  FF: '#FFB3AD',
  NNF: '#2EFF8C',
  VF: '#9E190C',
};

const legendItemStyle = item => ({
  backgroundColor: `${MOCK_ANALYSIS_COLORS[item]}`,
});

it('renders correctly', () => {
  const { container } = render(<PieLegend data={MOCK_DATA} itemStyle={legendItemStyle} />);
  expect(container).toMatchSnapshot();
});
