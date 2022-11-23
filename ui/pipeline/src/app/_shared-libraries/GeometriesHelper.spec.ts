import { getTextSizeForAreas } from './GeometriesHelper';

describe('GeometriesHelper.ts library', () => {
  beforeEach(() => {});

  it('should return nice font sizes', () => {
    const fontSizeFor0 = getTextSizeForAreas(0);
    const fontSizeFor10 = getTextSizeForAreas(10);
    const fontSizeFor100 = getTextSizeForAreas(100);
    const fontSizeFor1000 = getTextSizeForAreas(1000);
    const fontSizeFor10000 = getTextSizeForAreas(10000);
    const fontSizeFor100000 = getTextSizeForAreas(100000);
    const fontSizeFor1000000 = getTextSizeForAreas(1000000);
    const fontSizeFor10000000 = getTextSizeForAreas(10000000);
    const fontSizeFor100000000 = getTextSizeForAreas(100000000);
    expect(fontSizeFor0).toBe(1, 'Wrong font size for area 0');
    expect(fontSizeFor10).toBe(1, 'Wrong font size for area 10');
    expect(fontSizeFor100).toBe(1, 'Wrong font size for area 100');
    expect(fontSizeFor1000).toBe(1, 'Wrong font size for area 1000');
    expect(fontSizeFor10000).toBe(30, 'Wrong font size for area 10000');
    expect(fontSizeFor100000).toBe(100, 'Wrong font size for area 100000');
    expect(fontSizeFor1000000).toBe(200, 'Wrong font size for area 1000000');
    expect(fontSizeFor10000000).toBe(200, 'Wrong font size for area 10000000');
    expect(fontSizeFor100000000).toBe(200, 'Wrong font size for area 100000000');
  });
});
