import competitors from '../__fixtures__/competitors';
import categories from '../__fixtures__/categories';
import scores from '../__fixtures__/scores';
import competitorsUnits from '../__fixtures__/competitorsUnits';
import SpreadsheetUtils from './SpreadsheetUtils';

describe('SpreadsheetUtils class', () => {
  it('Builds headers as expected', () => {
    const headers = SpreadsheetUtils.buildHeaders(competitors);

    expect(headers).toEqual(['Category', 'Subcategory', 'Feature', competitors[0].name, competitors[1].name]);
  });

  it('Builds Total Score rows as expected', () => {
    const rows = SpreadsheetUtils.buildTotalScoreRows(categories, scores);

    const has = (value: RegExp) => expect.stringMatching(value);

    expect(rows).toEqual([
      [has(/Gesamtpunktzahl/i), '', '', String(scores[0].total), String(scores[1].total)],
      ['', has(/Auswertung aller Items/i), '', String(scores[0].total_program), String(scores[1].total_program)],
      [
        '',
        has(/Auswertung aller Archilyse-spezifischen Items/i),
        '',
        String(scores[0].total_archilyse),
        String(scores[1].total_archilyse),
      ],
      ['', has(/Anzahl Red Flags/i), '', 1, 1],
    ]);
  });

  it('Builds Total Prices rows as expected', () => {
    const rows = SpreadsheetUtils.buildTotalPricesRows(scores, competitorsUnits, 'CHF', true);

    const has = (value: RegExp) => expect.stringMatching(value);

    expect(rows).toEqual([
      [has(/Gesamtbruttomiete \/ Jahr/i), '', '', has(/CHF/i), has(/CHF/i)],
      ['', has(/Min. Ertrag \/ m²/i), '', has(/CHF\/m²/i), has(/CHF\/m²/i)],
      ['', has(/Durchschnittlicher Ertrag \/ m²/i), '', has(/CHF\/m²/i), has(/CHF\/m²/i)],
      ['', has(/Max. Ertrag \/ m²/i), '', has(/CHF\/m²/i), has(/CHF\/m²/i)],
    ]);
  });

  it('Builds Score values rows as expected', () => {
    const _categories = categories.slice(0, 1);
    const [category] = _categories;
    const [subSection] = category.sub_sections;
    const [dataFeature] = subSection.sub_sections;

    const has = (value: number) => expect.stringMatching(String(value));

    const rows = SpreadsheetUtils.buildScoreValuedRows(_categories, scores, competitors);

    expect(rows).toEqual([
      [category.name, '', '', scores[0][category.key], scores[1][category.key]],
      [],
      ['', subSection.name, '', has(scores[0][subSection.key]), has(scores[1][subSection.key])],
      ['', '', dataFeature.name, has(competitors[0][dataFeature.key]), has(competitors[1][dataFeature.key])],
      [],
    ]);
  });
});
