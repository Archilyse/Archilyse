import { UnitResponse } from '../types';
import PriceUtils from './PriceUtils';

describe('PriceUtils class', () => {
  it.each([
    [[null, undefined], 0],
    [[1, 2.5, undefined, null], 3.5],
    [[10, 20, 30, 40], 100],
  ])('total price of "%s" should be equal to %d', (prices, expected) => {
    const units = prices.map(price => ({ ph_gross_price: price } as UnitResponse));

    expect(PriceUtils.computeTotalPrice(units)).toBe(expected);
  });

  it.each([
    [[undefined, null], [10, 0], 0],
    [[3, 10], [undefined, null], 0],
    [[undefined, null, 3, 10], [10, 0, undefined, 2], 5],
    [[10, 200.5, undefined, null], [10, 20], 1],
    [[10, 20, 30, 40], [2, 5, 6, 10], 4],
  ])('min price per m2 of "%s" prices and "%s" areas should be equal to %d', (prices, areas, expected) => {
    const units = prices.map((price, index) => ({ ph_gross_price: price, net_area: areas[index] } as UnitResponse));

    expect(PriceUtils.findMinPricePerM2(units)).toBe(expected);
  });

  it.each([
    [[undefined, null], [10, 0], 0],
    [[3, 10], [undefined, null], 0],
    [[undefined, null, 3, 10], [10, 0, undefined, 2], 5],
    [[10, 200.5, undefined, null], [10, 20], 5.5125],
    [[10, 20, 30, 40], [2, 5, 6, 10], 4.5],
  ])('mean price per m2 of "%s" prices and "%s" areas should be equal to %d', (prices, areas, expected) => {
    const units = prices.map((price, index) => ({ ph_gross_price: price, net_area: areas[index] } as UnitResponse));

    expect(PriceUtils.findMeanPricePerM2(units)).toBe(expected);
  });

  it.each([
    [[undefined, null], [10, 0], 0],
    [[3, 10], [undefined, null], 0],
    [[undefined, null, 3, 10], [10, 0, undefined, 2], 5],
    [[10, 200.5, undefined, null], [10, 20], 10.025],
    [[10, 20, 30, 40], [2, 5, 6, 10], 5],
  ])('max price per m2 of "%s" prices and "%s" areas should be equal to %d', (prices, areas, expected) => {
    const units = prices.map((price, index) => ({ ph_gross_price: price, net_area: areas[index] } as UnitResponse));

    expect(PriceUtils.findMaxPricePerM2(units)).toBe(expected);
  });
});
