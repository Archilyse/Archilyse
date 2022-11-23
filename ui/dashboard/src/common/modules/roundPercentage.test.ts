import roundPercentage from './roundPercentage';

it.each([
  [null, undefined],
  [undefined, undefined],
  [0, '0%'],
  [0.003, '0.3%'],
  [0.003232, '0.32%'],
])('number %s should be rounded as %s', (percentage, result) => {
  expect(roundPercentage(percentage)).toBe(result);
});
