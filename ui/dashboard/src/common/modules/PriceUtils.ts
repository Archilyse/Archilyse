import { UnitResponse } from '../types';

type FormatPriceOptions = {
  currency?: string;
  style?: string;
};

class PriceUtils {
  static computeTotalPrice(units: UnitResponse[]): number {
    const cleanedPrices = units.filter(unit => typeof unit.ph_gross_price === 'number');

    return cleanedPrices.reduce((price, unit) => price + unit.ph_gross_price, 0);
  }

  static findPricesPerM2(units: UnitResponse[]): number[] {
    const cleanedUnits = PriceUtils._cleanFalsyUnits(units);

    return cleanedUnits.map(unit => unit.ph_gross_price / unit.net_area);
  }

  static findMinPricePerM2(units: UnitResponse[]): number {
    const prices = PriceUtils.findPricesPerM2(units);

    if (prices.length === 0) return 0;

    return Math.min(...prices);
  }

  static findMeanPricePerM2(units: UnitResponse[]): number {
    const prices = PriceUtils.findPricesPerM2(units);
    const total = PriceUtils.computeTotalPrice(prices.map(price => ({ ph_gross_price: price } as UnitResponse)));

    if (prices.length === 0) return 0;

    return total / prices.length;
  }

  static findMaxPricePerM2(units: UnitResponse[]): number {
    const prices = PriceUtils.findPricesPerM2(units);

    if (prices.length === 0) return 0;

    return Math.max(...prices);
  }

  static formatPrice(price: number, options = { currency: 'CHF' } as FormatPriceOptions): string {
    if (typeof price !== 'number') {
      return '-';
    }

    const formatter = new Intl.NumberFormat('en', {
      currency: options.currency || 'CHF',
      style: options.style,
    });

    return formatter.format(price);
  }

  static formatPricePerM2(price: number, currency: string): string {
    return `${PriceUtils.formatPrice(price, { currency: currency })} ${currency}/m²`;
  }

  static _cleanFalsyUnits = (units: UnitResponse[]): UnitResponse[] => {
    return units.filter(unit => typeof unit.ph_gross_price === 'number' && Boolean(unit.net_area));
  };
}

export default PriceUtils;
