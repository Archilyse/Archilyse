import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { PAGE_SIZES, RESCALE_NOT_ALLOWED_MESSAGE } from '../../../constants';
import ActionButtons from './action-buttons';

const MOCK_POINTS = [
  { x: 72, y: 506 },
  { x: 416, y: 476 },
];

const MOCK_MEASUREMENTS = [
  {
    distance: 4.31,
    areaSize: 0,
    points: [
      { x: -361, y: 570 },
      { x: -9, y: 564 },
    ],
    scaleFactor: 1.49,
  },
  {
    distance: 4.3,
    areaSize: 0,
    points: [
      { x: -361, y: 570 },
      { x: -9, y: 564 },
    ],
    scaleFactor: 1.49,
  },
];
const MOCK_PAPER_FORMAT = Object.keys(PAGE_SIZES)[0];
const MOCK_SCALE_RATIO = 5;

const MOCK_PROPS = {
  background: {
    width: 1200,
    height: 800,
    rotation: 0,
    shift: { x: 0, y: 0 },
  },
  scaleAllowed: true,
  scaleRatio: null,
  paperFormat: '',
  measurements: [],
  onSaveMeasure: () => {},
  onSaveScale: () => {},
  onClear: () => {},
  points: [],
};

describe('Action buttons component', () => {
  const renderComponent = (changedProps = {}) => {
    const props = { ...MOCK_PROPS, ...changedProps };
    return render(<ActionButtons {...props} />);
  };

  describe('With an already scaled plan', () => {
    it('Renders a disabled button', () => {
      renderComponent({ scaleAllowed: false });
      expect(screen.getByText(new RegExp(RESCALE_NOT_ALLOWED_MESSAGE))).toBeInTheDocument();
    });
  });

  describe('With a not scaled plan', () => {
    describe('Initially without measures or page specs', () => {
      it('Does not render buttons', () => {
        renderComponent();
        expect(screen.queryByText(/Save/)).not.toBeInTheDocument();
        expect(screen.queryByText(/Clear/)).not.toBeInTheDocument();
      });
    });

    describe('Entering measures', () => {
      it('If it does not have enough measures and is drawing, renders a button to save the measures', () => {
        renderComponent({ measurements: [], points: MOCK_POINTS });
        const saveButton = screen.getByText(/Save measure/);
        expect(saveButton).toBeInTheDocument();
        expect(saveButton).not.toBeDisabled();
      });

      it('If it does not have enough measures and is not drawing, renders a disabled button to save measures', () => {
        renderComponent({ measurements: MOCK_MEASUREMENTS.slice(0, 1) });
        const saveButton = screen.getByText(/Save measure/);
        expect(saveButton).toBeInTheDocument();
        expect(saveButton).toBeDisabled();
      });

      it('If it does have enough measures, it automatically sets the plan scale with no need to click an extra button, so no buttons are rendered after then', () => {
        renderComponent({ measurements: MOCK_MEASUREMENTS });
        expect(screen.queryByText(/Save/)).not.toBeInTheDocument();
        expect(screen.queryByText(/Clear/)).not.toBeInTheDocument();
      });

      it('If one of the measures is incorrect, renders a button to repeat the measure', () => {
        const incorrectMeasurement = {
          ...MOCK_MEASUREMENTS[0],
          distance: 1000, // To have a scale different from the other measure
        };
        const measurements = [MOCK_MEASUREMENTS[0], incorrectMeasurement];

        renderComponent({ measurements });
        expect(screen.getByText(/Repeat current measurement/)).toBeInTheDocument();
      });
    });

    describe('Entering page specs', () => {
      it('Renders a button to validate the scale', () => {
        renderComponent({ paperFormat: MOCK_PAPER_FORMAT, scaleRatio: MOCK_SCALE_RATIO });
        expect(screen.getByText(/Validate scale using format\/ratio/)).toBeInTheDocument();
      });
    });

    describe('Entering measures AND page specs', () => {
      it('Renders a button to validate page specs and a warning when the scales are different', () => {
        renderComponent({
          paperFormat: MOCK_PAPER_FORMAT,
          scaleRatio: MOCK_SCALE_RATIO,
          measurements: MOCK_MEASUREMENTS,
        });
        expect(screen.getByText(/Validate scale using format\/ratio/)).toBeInTheDocument();
        expect(
          screen.getByText(/Please note that scale from measure is different from the page specs one/)
        ).toBeInTheDocument();
      });
      it('Renders a button to validate page specs if scales are the same', () => {
        renderComponent({
          paperFormat: MOCK_PAPER_FORMAT,
          scaleRatio: 12, // To make the scale as the same as in MOCK_MEASUREMENTS
          measurements: MOCK_MEASUREMENTS,
        });
        expect(screen.getByText(/Validate scale using format\/ratio/)).toBeInTheDocument();
        expect(
          screen.queryByText(/Please note that scale from measure is different from the page specs one/)
        ).not.toBeInTheDocument();
      });
    });
  });
});
