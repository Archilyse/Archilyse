import * as React from 'react';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Form from './index';

afterEach(cleanup);

describe('Form component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(<Form {...props} />);
  };
  beforeEach(() => {
    props = {
      fields: {},
      onSubmit: () => {},
    };
  });

  describe('Password field', () => {
    const fields = [{ name: 'password', type: 'password', label: 'Password', passwordValidation: true }];

    it('Toggles visibility on clicking on the adornment', () => {
      renderComponent({ fields });

      // By default the input does not show the password
      const passwordField = screen.getByLabelText(/Password/);
      expect(passwordField).toHaveAttribute('type', 'password');

      // On click toggle icon, the password content will be shown
      userEvent.click(screen.getByTestId('toggle-visibility-icon'));
      expect(passwordField).toHaveAttribute('type', 'text');

      // Toggle again restore the status
      userEvent.click(screen.getByTestId('toggle-visibility-icon'));
      expect(passwordField).toHaveAttribute('type', 'password');
    });

    it('Sets the password as valid: Medium strength', () => {
      renderComponent({ fields });
      const validPassword = 'aDf1324!';
      const passwordField = screen.getByLabelText(/Password/);
      fireEvent.change(passwordField, { target: { value: validPassword } });
      expect(screen.getByTestId('valid-password')).toBeInTheDocument();
    });

    it('Sets the password as valid: Strong strength', () => {
      renderComponent({ fields });
      const validPassword = 'aDf1324,9b.asd111';
      const passwordField = screen.getByLabelText(/Password/);
      fireEvent.change(passwordField, { target: { value: validPassword } });
      expect(screen.getByTestId('valid-password')).toBeInTheDocument();
    });

    it('Sets the password as invalid', () => {
      renderComponent({ fields });
      const inValidPassword = 'payaso';
      const passwordField = screen.getByLabelText(/Password/);
      fireEvent.change(passwordField, { target: { value: inValidPassword } });
      expect(screen.getByTestId('invalid-password')).toBeInTheDocument();
    });

    it('Do not enfoce validation when required explicitly', () => {
      const fields = [{ name: 'password', type: 'password', label: 'Password', passwordValidation: false }];
      renderComponent({ fields });
      expect(screen.queryByText('One lowercase character')).not.toBeInTheDocument();
    });

    const WRONG_VALIDATION_TEST_CASES = [
      ['One lowercase character', 'A'],
      ['One uppercase character', 'b'],
      ['One number', 'A'],
      ['One special character', 'a'],
      ['8 characters minimum', 'abc'],
    ];

    it.each(WRONG_VALIDATION_TEST_CASES)('Enforce validation rule: %s', (rule, wrongInput) => {
      renderComponent({ fields });
      const passwordField = screen.getByLabelText(/Password/);
      fireEvent.change(passwordField, { target: { value: wrongInput } });
      const ruleText = screen.getByText(new RegExp(rule));
      expect(ruleText).not.toHaveStyle({ color: 'green' });
    });

    const SUCCESS_VALIDATION_TEST_CASES = [
      ['One lowercase character', 'a'],
      ['One uppercase character', 'A'],
      ['One number', '1'],
      ['One special character', '!'],
      ['8 characters minimum', '12345678'],
    ];

    it.each(SUCCESS_VALIDATION_TEST_CASES)('Show success validation rule: %s', (rule, validInput) => {
      renderComponent({ fields });
      const passwordField = screen.getByLabelText(/Password/);
      fireEvent.change(passwordField, { target: { value: validInput } });
      const ruleText = screen.getByText(new RegExp(rule));
      expect(ruleText).toHaveStyle({ color: 'green' });
    });
  });
});
