import capitalize from './capitalize';

describe('Capitalize module', () => {
  it('Capitalizes a word', () => {
    const TEST_WORD = 'ola';
    const result = capitalize(TEST_WORD);
    expect(result[0]).toBe(TEST_WORD[0].toUpperCase());
  });

  it.each([[null], [undefined], ['']])('Returns an empty string when receiving %s', falsyValue => {
    expect(capitalize(falsyValue)).toBe('');
  });
});
