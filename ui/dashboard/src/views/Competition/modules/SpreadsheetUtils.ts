import XLSX from 'xlsx/xlsx.mini';
import {
  CompetitionMainCategoryResponseType,
  CompetitionScoresResponseType,
  CompetitorResponseType,
  CompetitorsUnitsResponse,
} from '../../../common/types';
import TableUtils from '../components/competitionTable/TableUtils';

/**
 * Example of the spreadsheet structure:
 * [
 *   [Category, Subcategory, Feature, Competitor Name 1, Competitor Name 2],
 *   ['Architecture Overview', '', '', 10, 5],
 *   ['', 'Residential Share', '', 6, 4],
 *   ['', '', 'Evaluation residential use', 10, 5],
 * ]
 *
 * We have this data structure: category <- subcategory <- data feature (arrow means the item is child of the other)
 * Therefore first 3 columns are reserved for displaying  this hierarchy
 * Then all the rest columns are competitors data
 */
class SpreadsheetUtils {
  static buildHeaders = (competitors: CompetitorResponseType[]): string[] => {
    const competitorsNames = competitors.map(competitor => competitor.name);

    return ['Category', 'Subcategory', 'Feature', ...competitorsNames];
  };

  static buildTotalScoreRows = (
    categories: CompetitionMainCategoryResponseType[],
    scores: CompetitionScoresResponseType[]
  ): (string | number)[][] => {
    const [total, architectureProgramme, archilyse, numberOfRedFlags] = TableUtils.buildTotalScoresRows(
      scores,
      categories
    );

    return [
      [total.title, '', '', ...total.formatted],
      ['', architectureProgramme.title, '', ...architectureProgramme.formatted],
      ['', archilyse.title, '', ...archilyse.formatted],
      ['', numberOfRedFlags.title, '', ...numberOfRedFlags.formatted],
    ];
  };

  static buildTotalPricesRows = (
    scores: CompetitionScoresResponseType[],
    competitorsUnits: CompetitorsUnitsResponse[],
    currency: string,
    prices_are_rent: boolean
  ): string[][] => {
    const [total, min, mean, max] = TableUtils.buildTotalPricesRows(
      scores,
      competitorsUnits,
      currency,
      prices_are_rent
    );

    return [
      [total.title, '', '', ...total.formatted],
      ['', min.title, '', ...min.formatted],
      ['', mean.title, '', ...mean.formatted],
      ['', max.title, '', ...max.formatted],
    ];
  };

  static buildScoreValuedRows = (
    categories: CompetitionMainCategoryResponseType[],
    scores: CompetitionScoresResponseType[],
    competitors: CompetitorResponseType[]
  ): (string | number)[][] => {
    const rows: (string | number)[][] = [];

    categories.forEach(category => {
      const data = scores.map(score => score[category.key]);
      rows.push([category.name, '', '', ...data]);

      category.sub_sections.forEach((subCategory, subCategoryIndex) => {
        if (subCategoryIndex === 0) rows.push([]); // inserts new row

        const data = scores.map(score => TableUtils.formatScore(score[subCategory.key]));
        rows.push(['', subCategory.name, '', ...data]);

        subCategory.sub_sections.forEach((dataFeature, index) => {
          const data = scores.map(score => {
            const rawData = TableUtils.findInCompetitors(score.id, competitors, dataFeature.key);
            const formattedRawData = TableUtils.formatRawData(rawData, dataFeature.unit, dataFeature.key);
            return formattedRawData;
          });

          rows.push(['', '', dataFeature.name, ...data]);

          if (index === subCategory.sub_sections.length - 1) rows.push([]); // inserts new row
        });
      });
    });

    return rows;
  };

  static buildAllRows = (
    categories: CompetitionMainCategoryResponseType[],
    scores: CompetitionScoresResponseType[],
    competitors: CompetitorResponseType[],
    competitorsUnits: CompetitorsUnitsResponse[],
    currency: string,
    prices_are_rent: boolean
  ): (string | number)[][] => {
    const orderedCompetitors = TableUtils.orderCompetitorByScore(scores, competitors);

    const headers = SpreadsheetUtils.buildHeaders(orderedCompetitors);
    const totalScoreRows = SpreadsheetUtils.buildTotalScoreRows(categories, scores);
    const totalPricesRows = SpreadsheetUtils.buildTotalPricesRows(scores, competitorsUnits, currency, prices_are_rent);
    const scoreValuesRows = SpreadsheetUtils.buildScoreValuedRows(categories, scores, competitors);

    return [headers, [], ...totalScoreRows, [], ...totalPricesRows, [], ...scoreValuesRows];
  };

  static download = (rows: (string | number)[][]): void => {
    const ws = XLSX.utils.aoa_to_sheet(rows);

    const headers = rows[0];
    const competitorsNames = headers.slice(3);

    ws['!cols'] = [{ width: 20 }, { width: 25 }, { width: 40 }, ...competitorsNames.map(() => ({ width: 20 }))];

    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Results Table');
    XLSX.writeFile(wb, 'Competition-Tool-Results.xlsx');
  };
}

export default SpreadsheetUtils;
