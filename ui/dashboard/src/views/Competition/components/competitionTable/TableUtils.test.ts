import categories from '../../__fixtures__/categories';
import scores from '../../__fixtures__/scores';
import TableUtils from './TableUtils';

describe('TableUtils class', () => {
  it.each([
    [null, undefined, '-'],
    [{ bullshit: 'bullshit' }, undefined, '-'],
    [[], undefined, '-'],
    [50, undefined, '50'],
    [2.333334, undefined, '2.3'],
    [0.2, '%', '20%'],
    [2.33, 'time_delta', '2 hour(s) 20 min(s)'],
    [5, 'time_delta', '5 hour(s)'],
    [0.2, 'time_delta', '12 min(s)'],
    [1.996, 'time_delta', '2 hour(s)'],
    [0, 'time_delta', '0'],
    [0.0654345, 'lx', '0.065 lx'],
    [0.0003, 'lx', '0 lx'],
    [0.0005, 'lx', '0.001 lx'],
    [0.0003, 'sr', '0 sr'],
    [0.0005, 'sr', '0.001 sr'],
    [0.0003, 'x', '0x'],
    [0.0005, 'x', '0.001x'],
    [0.2, 'cm', '0.2 cm'],
    [0.2, 'any boolshit', '0.2 any boolshit'],
    [true, undefined, 'Yes'],
    [false, 'boolean', 'No'],
  ])('with given "%o" score and "%s" unit should display "%s"', (value: any, unitType, expected) => {
    expect(TableUtils.formatRawData(value, unitType)).toBe(expected);
  });

  it.each([
    [true, [true, false, false], true],
    [false, [true, false], false],
    [1, [1, 2, 3, 4], false],
    [3, [1, 2, 3, 4], false],
    [4, [1, 2, 3, 4], true],
  ])('is %s maximum value in %s? %s', (currentValue, values, expected) => {
    expect(TableUtils.isMaxValue(currentValue, values)).toBe(expected);
  });

  it.each([
    [true, [true, false, false], false],
    [false, [true, false], true],
    [1, [1, 2, 3, 4], true],
    [3, [1, 2, 3, 4], false],
    [4, [1, 2, 3, 4], false],
  ])('is %s minimum value in %s? %s', (currentValue, values, expected) => {
    expect(TableUtils.isMinValue(currentValue, values)).toBe(expected);
  });

  it('should count number of active red flags', () => {
    expect(TableUtils.countNumberOfActiveRedFlags(categories, scores[1])).toBe(1);
  });
});
