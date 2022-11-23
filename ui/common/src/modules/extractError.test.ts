import extractError from './extractError';

it.each([
  [null, 'Some error occurred. Try again later'],
  [{ key: 1 }, 'Some error occurred. Try again later'],
  [{ response: [1, 2, 3] }, 'Some error occurred. Try again later'],
  [{ response: { data: 1 } }, 'Some error occurred. Try again later'],
  [{ response: { data: { msg: 'Error has happened' } } }, 'Error has happened'],
  [{ response: { data: { message: 'Error has happened' } } }, 'Error has happened'],
  [null, 'Some error occurred. Try again later'],
])('with %o response should return %s', (error, result) => {
  expect(extractError(error as any)).toBe(result);
});
