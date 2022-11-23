import DateUtils from './dateUtils';

beforeEach(() => {
  jest.useFakeTimers('modern');
  jest.setSystemTime(new Date(2021, 0, 1));
});

afterEach(() => {
  jest.useRealTimers();
});

it.each([
  [null, '-'],
  [undefined, '-'],
  ['2021-05-14T09:26:18.379Z', '9:26:18 AM'],
  ['2021-05-14T21:26:18.379Z', '9:26:18 PM'],
])('gets time from ISO string correctly: %s -> %s', (isoString, result) => {
  expect(DateUtils.getTimeFromISOString(isoString)).toBe(result);
});

it.each([
  [null, '-'],
  [undefined, '-'],
  ['2021-05-14T09:26:18.379Z', '5/14/2021'],
])('gets date from ISO string correctly: %s -> %s', (isoString, result) => {
  expect(DateUtils.getDateFromISOString(isoString)).toBe(result);
});

it.each([
  [null, '-'],
  [undefined, '-'],
  ['2021-05-14T09:26:18.379Z', '5/14/2021, 9:26:18 AM'],
])('gets date from ISO string correctly: %s -> %s', (isoString, result) => {
  expect(DateUtils.getFullDateFromISOString(isoString)).toBe(result);
});
