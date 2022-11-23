import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { MOCK_VALIDATION_ERRORS } from '../../tests/utils/';
import { COLORS } from '../../constants';
import ValidationErrors from './validationErrors';

describe('<ValidationErrors /> component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };

    return render(<ValidationErrors {...props} />);
  };

  beforeEach(() => {
    props = {
      errors: MOCK_VALIDATION_ERRORS,
      highlightedError: '',
    };
  });

  it('Renders correctly when there are no errors', () => {
    renderComponent({ errors: [] });
    expect(screen.queryByTestId(/error-circle/)).not.toBeInTheDocument();
  });

  it('Displays a set of blocking & non-blocking errors', () => {
    renderComponent();
    MOCK_VALIDATION_ERRORS.forEach((error, index) => {
      const errorNumber = index + 1;
      expect(screen.getByText(errorNumber)).toBeInTheDocument();
      expect(screen.getByTestId(`error-circle-${errorNumber}`)).toHaveAttribute(
        'fill',
        error.is_blocking ? 'red' : 'yellow'
      );
    });
  });

  it('Higlights an error', () => {
    const MOCK_HIGHLIGHTED_ERROR = MOCK_VALIDATION_ERRORS[0].object_id;
    renderComponent({ highlightedError: MOCK_HIGHLIGHTED_ERROR });

    MOCK_VALIDATION_ERRORS.forEach((error, index) => {
      const errorNumber = index + 1;
      const isHighlighted = error.object_id === MOCK_HIGHLIGHTED_ERROR;
      if (isHighlighted) {
        expect(screen.getByTestId(`error-circle-${errorNumber}`)).toHaveAttribute('fill', COLORS.PRIMARY_COLOR);
      } else {
        expect(screen.getByTestId(`error-circle-${errorNumber}`)).toHaveAttribute(
          'fill',
          expect.not.stringContaining(COLORS.PRIMARY_COLOR)
        );
      }
    });
  });
});
