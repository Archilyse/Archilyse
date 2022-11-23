import { AxiosError } from 'axios';

export default (error: AxiosError, fallbackText = 'Some error occurred. Try again later'): string => {
  const parsedError = error?.response?.data?.msg || error?.response?.data?.message || fallbackText;
  return parsedError && typeof parsedError === 'object' ? JSON.stringify(parsedError) : parsedError;
};
