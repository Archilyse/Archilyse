import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { MOCK_CONTEXT } from '../../tests/utils';
import { GeometryUtils } from '../../utils/export';
import Ruler from './ruler';

const MOCK_SCALE = 2;
describe('Ruler component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };

    return render(<Ruler {...props} />);
  };

  beforeEach(() => {
    props = {
      length: 0,
      unit: '',
      transform: '',
      scale: MOCK_SCALE,
      scalingWithOneLine: false,
    };
  });

  it('Renders the length in cms correctly', () => {
    const MOCK_LENGTH = 20;
    const MOCK_UNIT = 'cm';
    const { planScale } = MOCK_CONTEXT;

    renderComponent({ length: MOCK_LENGTH, unit: MOCK_UNIT });

    const expectedSize = GeometryUtils.convertPixelsToCMs(planScale, MOCK_LENGTH).toFixed(2);
    const expectedText = `${expectedSize} ${MOCK_UNIT}`;
    expect(screen.getByText(new RegExp(expectedText))).toBeInTheDocument();
  });

  it('Renders the scale tool length if we are scaling with one line', () => {
    const MOCK_LENGTH = 20;
    const MOCK_SCALE_TOOL = { distance: 15.5 };
    const MOCK_UNIT = 'm';

    renderComponent({
      length: MOCK_LENGTH,
      unit: MOCK_UNIT,
      scalingWithOneLine: true,
      scaleTool: MOCK_SCALE_TOOL,
    });

    const expectedText = `${MOCK_SCALE_TOOL.distance} ${MOCK_UNIT}`;
    expect(screen.getByText(new RegExp(expectedText))).toBeInTheDocument();
  });
});
