import * as React from 'react';
import { render, screen } from '@testing-library/react';
import {
  REQUEST_STATUS_BY_ACTION,
  SCALING_MAX_DIFF_BETWEEN_MEASUREMENTS,
  SCALING_REQUIRED_MEASUREMENT_COUNT,
} from '../../../constants';
import { toFixedFloat } from '../../../utils/math';
import ScaleMeasurements, { OUTLIER_STYLE, VALID_STYLE } from './scale-measurements';
import { calculateScale } from './utils';

const MOCK_SCALE_TOOL = {
  distance: 0,
  areaSize: 0,
  points: [],
  userHasChangedMeasures: false,
};

const MOCK_PROPS = {
  scaleTool: MOCK_SCALE_TOOL,
  measurements: [],
  floorScales: [],
  floorScalesRequest: { [REQUEST_STATUS_BY_ACTION.FETCH_FLOOR_SCALES]: {} },
};

describe('Scale measurements component', () => {
  const renderComponent = (props = MOCK_PROPS) => {
    return render(<ScaleMeasurements {...props} />);
  };

  it('shows a list of blank measurements to fill if no measurements have been passed', () => {
    renderComponent();
    const measuresToTake = Array.from(Array(SCALING_REQUIRED_MEASUREMENT_COUNT).keys());

    for (const index of measuresToTake) {
      const expectedText = screen.getByText(new RegExp(`Measurement #${index + 1}:`));
      expect(expectedText).toBeInTheDocument();

      expect(expectedText).not.toHaveStyle(VALID_STYLE);
      expect(expectedText).not.toHaveStyle(OUTLIER_STYLE);
    }
  });

  it('shows n entries filled by n measurements done successfully', () => {
    const points = [
      { x: 0, y: 1000 },
      { x: 0, y: 1500 },
    ];
    const MOCK_MEASUREMENTS = [
      { points, distance: 10.4, areaSize: 0, area: null },
      { points, distance: 10.45, areaSize: 0, area: null },
    ];

    renderComponent({
      ...MOCK_PROPS,
      measurements: MOCK_MEASUREMENTS,
    });

    for (const measurement of MOCK_MEASUREMENTS) {
      const scaleFactor = toFixedFloat(calculateScale(measurement), 2);
      const measurementEntry = screen.getByText(content => content.endsWith(`${scaleFactor}`));
      expect(measurementEntry).toBeInTheDocument();
      expect(measurementEntry.parentElement.parentElement).toHaveStyle(VALID_STYLE);
    }
  });

  it(`displays an invalid measurement if relative diff between measurements > ${SCALING_MAX_DIFF_BETWEEN_MEASUREMENTS}`, () => {
    const points = [
      { x: 0, y: 1000 },
      { x: 0, y: 1500 },
    ];

    const MOCK_MEASUREMENTS = [
      { points, distance: 10.4, areaSize: 0, area: null },
      { points, distance: 20.5, areaSize: 0, area: null },
    ];

    renderComponent({
      ...MOCK_PROPS,
      measurements: MOCK_MEASUREMENTS,
    });

    const [firstMeasurement, secondMeasurement] = MOCK_MEASUREMENTS;

    //  First measure will be valid
    const firstScaleFactor = toFixedFloat(calculateScale(firstMeasurement), 2);

    const firstMeasurementEntry = screen.getByText(content => content.endsWith(`${firstScaleFactor}`));
    expect(firstMeasurementEntry).toBeInTheDocument();
    expect(firstMeasurementEntry.parentElement.parentElement).toHaveStyle(VALID_STYLE);

    // Second one will not
    const secondScaleFactor = toFixedFloat(calculateScale(secondMeasurement), 2);

    const secondMeasurementEntry = screen.getByText(content => content.endsWith(`${secondScaleFactor}`));
    expect(secondMeasurementEntry).toBeInTheDocument();
    expect(secondMeasurementEntry.parentElement.parentElement).toHaveStyle(OUTLIER_STYLE);
  });
});
