import * as React from 'react';
import userEvent from '@testing-library/user-event';
import { render, screen } from '@testing-library/react';

import FormNumberInput from './form-number-input';

const EXPECTED_ERROR_MESSAGE = 'Only incr of 1 allowed (1, 2, 3...)';

describe('FormNumberInput component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };

    return render(<FormNumberInput {...props} />);
  };

  beforeEach(() => {
    props = {
      value: 10,
      style: '',
      onChange: () => {},
      onValid: () => {},
    };
  });

  it('Shows the initial value passed as prop', () => {
    const INITIAL_VALUE = '90';
    renderComponent({ value: INITIAL_VALUE });

    expect(screen.getByDisplayValue(INITIAL_VALUE)).toBeInTheDocument();
  });

  it.each([['38.5'], ['4.2'], ['11.3'], ['1.2']])('Shows an error with incorrect value: %s', async incorrectInput => {
    const INITIAL_VALUE = '30';
    renderComponent({ value: INITIAL_VALUE });

    const input = screen.getByDisplayValue(INITIAL_VALUE);
    userEvent.clear(input);
    userEvent.type(input, incorrectInput);

    expect(screen.getByText(EXPECTED_ERROR_MESSAGE)).toBeInTheDocument();
  });

  it.each([['5'], ['10'], ['15'], ['20'], ['21']])('Renders correct value without error: %s', async correctInput => {
    const INITIAL_VALUE = '30';
    const onValid = jest.fn();
    const onChange = jest.fn();
    renderComponent({ value: INITIAL_VALUE, onValid, onChange });

    const input = screen.getByDisplayValue(INITIAL_VALUE);
    userEvent.clear(input);
    userEvent.type(input, correctInput);

    expect(screen.queryByText(EXPECTED_ERROR_MESSAGE)).not.toBeInTheDocument();
    expect(onValid).toBeCalled();
    expect(onChange).toBeCalled();
  });
});
