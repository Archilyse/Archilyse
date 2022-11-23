import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { RequestStatusType } from '../../constants';
import { FloorScale } from '../../types';
import FloorMeasures from './FloorMeasures';

const MOCK_FLOOR_SCALES: FloorScale[] = [
  { floorNumber: 0, planId: 54, scale: 2.8658785342051996 },
  { floorNumber: 1, planId: 55, scale: 0.7973811060482169 },
  { floorNumber: 3, planId: 57, scale: 0.9963753382273872 },
  { floorNumber: 4, planId: 58, scale: 0.9999762196354438 },
  { floorNumber: 5, planId: 59, scale: 9.534569706533716 },
  { floorNumber: 6, planId: 60, scale: 0.9998000599800071 },
  { floorNumber: 7, planId: 61, scale: 1.037654785442913 },
  { floorNumber: 8, planId: 62, scale: 0.9999989882838208 },
];

const MOCK_LINE_POINTS = [
  { x: -630.18, y: -139.6 },
  { x: 98.82, y: -120.16 },
];

const MOCK_POLYGON_POINTS = [
  { x: 308.98, y: 371.14 },
  { x: 557.63, y: 552.15 },
  { x: 560.71, y: 545.31 },
  { x: 661.85, y: 319.95 },
  { x: 313.31, y: 365.21 },
  { x: 661.85, y: 319.95 },
];

describe('FloorMeasures', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(<FloorMeasures {...props} />);
  };

  beforeEach(() => {
    props = {
      floorScales: [],
      points: [],
      requestStatus: {},
    };
  });

  it('When there are not any other floors, it does not render anything', () => {
    renderComponent({
      floorScales: [],
      points: MOCK_LINE_POINTS,
      requestStatus: { status: RequestStatusType.FULFILLED },
    });
    expect(screen.queryByText(/Same line in:/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Same polygon in:/)).not.toBeInTheDocument();
  });

  it('When fetching the data, shows a spinner and a text with info', () => {
    renderComponent({
      floorScales: [],
      points: MOCK_LINE_POINTS,
      requestStatus: { status: RequestStatusType.PENDING },
    });
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Loading comparison with other floors...')).toBeInTheDocument();
  });

  it('Display how the same line is measured in other floors', () => {
    renderComponent({ floorScales: MOCK_FLOOR_SCALES, points: MOCK_LINE_POINTS });
    expect(screen.getByText(/Same line in:/)).toBeInTheDocument();

    // Ensure we display every floor info
    for (const floor of MOCK_FLOOR_SCALES) {
      expect(screen.getByText(`Floor: ${floor.floorNumber} - (${floor.planId}):`));
    }
    // Ensure we display the measure for the floors, showing a number and the unit (m)
    const anyNumberWithDecimals = /^\d*\.\d*$/;
    expect(screen.getAllByText(anyNumberWithDecimals).length).toBe(MOCK_FLOOR_SCALES.length);
    expect(screen.getAllByText(/^m$/).length).toBe(MOCK_FLOOR_SCALES.length);
  });

  it('Displays how the same polygon is measured in other floors', () => {
    renderComponent({ floorScales: MOCK_FLOOR_SCALES, points: MOCK_POLYGON_POINTS });
    expect(screen.getByText(/Same polygon in:/)).toBeInTheDocument();

    // Ensure we display every floor info
    for (const floor of MOCK_FLOOR_SCALES) {
      expect(screen.getByText(`Floor: ${floor.floorNumber} - (${floor.planId}):`));
    }
    // Ensure we display the measure for the floors, showing a number and the unit (m2)
    const anyNumberWithDecimals = /^\d*\.\d*$/;
    expect(screen.getAllByText(anyNumberWithDecimals).length).toBe(MOCK_FLOOR_SCALES.length);
    expect(screen.getAllByText(/^m$/).length).toBe(MOCK_FLOOR_SCALES.length);
    expect(screen.getAllByText(/^2$/).length).toBe(MOCK_FLOOR_SCALES.length);
  });

  it('When fetching the data, shows a spinner and a text with info', () => {
    renderComponent({
      floorScales: [],
      points: MOCK_LINE_POINTS,
      requestStatus: { status: RequestStatusType.PENDING },
    });
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Loading comparison with other floors...')).toBeInTheDocument();
  });

  it('Displays an error in a given floor if it scale info could not be fetch', () => {
    const floorScales = MOCK_FLOOR_SCALES.slice(0, 7);
    floorScales.push({ floorNumber: 8, planId: 62, scale: 0, error: 'BAM! War is here' });
    renderComponent({ floorScales: floorScales, points: MOCK_LINE_POINTS });

    expect(screen.getByText(/Error fetching info/)).toBeInTheDocument();

    const anyNumberWithDecimals = /^\d*\.\d*$/;
    expect(screen.getAllByText(anyNumberWithDecimals).length).toBe(MOCK_FLOOR_SCALES.length - 1);
    expect(screen.getAllByText(/^m$/).length).toBe(MOCK_FLOOR_SCALES.length - 1);
  });
});
