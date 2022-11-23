import { displayValidationHttpError, isValidationError } from 'Components/ErrorBoundary';

const getErrorMessage = error => {
  if (isValidationError(error)) {
    return displayValidationHttpError(error);
  }
  return (error.response && error.response.data && error.response.data.msg) || error?.toString() || '';
};

export default getErrorMessage;
