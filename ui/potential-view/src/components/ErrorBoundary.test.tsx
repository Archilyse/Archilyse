import * as React from 'react';
import { render, screen } from '@testing-library/react';
import * as Sentry from '@sentry/browser';
import ErrorBoundary, { handleNetworkError } from './ErrorBoundary';

jest.mock('@sentry/browser');
jest.mock('axios', () => jest.requireActual('axios'));

const ComponentWithGenericError = () => {
  throw new Error('Generic error!AHHH PANIC!');
  return <p>salpica</p>;
};

const renderComponent = (ChildComponent: any) => {
  return render(
    <ErrorBoundary>
      <ChildComponent />
    </ErrorBoundary>
  );
};

describe('Error Boundary component', () => {
  it('Displays a generic error message on an expected error inside a component', () => {
    const EXPECTED_ERROR_MESSAGE = 'Something went wrong, please contact technical support.';
    renderComponent(ComponentWithGenericError);

    const sentrySpy = jest.spyOn(Sentry, 'withScope');
    expect(sentrySpy).toHaveBeenCalled();
    expect(screen.getByText(EXPECTED_ERROR_MESSAGE)).toBeInTheDocument();
  });
});

describe('handleNetworkError', () => {
  it('Shows a message to the user on server error and calls sentry', () => {
    const context = { show: jest.fn() };
    const error = { response: { status: 502 } };
    const EXPECTED_ERROR_MESSAGE = `Sorry, there was an error on the server: ${error.response.status}`;
    const sentrySpy = jest.spyOn(Sentry, 'captureException');

    expect(() => handleNetworkError(error, context)).toThrowError();

    expect(sentrySpy).toHaveBeenCalled();
    expect(context.show).toHaveBeenCalledWith({ message: EXPECTED_ERROR_MESSAGE, severity: 'error' });
  });
  it('Shows a generic error message on other codes', () => {
    const EXPECTED_ERROR_MESSAGE = `Sorry, I'm a teapot`;
    const context = { show: jest.fn() };
    const error = { response: { status: 418 }, toString: () => EXPECTED_ERROR_MESSAGE };

    expect(() => handleNetworkError(error, context)).toThrowError();
    expect(context.show).toHaveBeenCalledWith({ message: EXPECTED_ERROR_MESSAGE, severity: 'error' });
  });
});
