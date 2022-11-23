const SWISS_GERMAN_LOCALE = 'de-CH';

export default (price: number): string => {
  const roundedPrice = parseFloat(price.toFixed(2));
  return new Intl.NumberFormat(SWISS_GERMAN_LOCALE).format(roundedPrice);
};
