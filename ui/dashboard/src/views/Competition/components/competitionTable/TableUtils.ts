import PriceUtils from '../../../../common/modules/PriceUtils';
import {
  CompetitionItemResponseType,
  CompetitionMainCategoryResponseType,
  CompetitionScoresResponseType,
  CompetitorResponseType,
  CompetitorsUnitsResponse,
} from '../../../../common/types';
import CUSTOM_FEATURE_NAME from '../customFeatureTitle';

class TableUtils {
  static findInCompetitors = (
    scoreId: number,
    competitors: CompetitorResponseType[],
    key: string
  ): number | boolean | string => {
    const competitor = competitors.find(competitor => competitor.id === scoreId);

    if (competitor) return competitor[key];

    return '-';
  };

  static orderCompetitorByScore = (
    scores: CompetitionScoresResponseType[],
    competitors: CompetitorResponseType[]
  ): CompetitorResponseType[] => {
    return scores.map(score => competitors.find(competitor => competitor.id === score.id));
  };

  static orderCompetitorUnitsByScore = (
    scores: CompetitionScoresResponseType[],
    competitorsUnits: CompetitorsUnitsResponse[]
  ): CompetitorsUnitsResponse[] => {
    return scores.map(score => competitorsUnits.find(unit => unit.competitor_id === score.id));
  };

  static formatScore = (value: number | boolean | string, unitType?: string, featureKey?: string): string => {
    if (typeof value === 'number') {
      if (unitType === '%') {
        return (value * 100).toFixed();
      }

      if (unitType === 'time_delta') {
        return TableUtils.convertDecimalHoursIntoTime(value);
      }

      if (['lx', 'sr', 'x'].includes(unitType)) {
        const rounded = value.toFixed(3); // show more decimals as this number usually too small

        if (Number(rounded) === 0) return '0';

        return rounded;
      }

      const roundedValue = value.toFixed(1);
      const isEndsWithZero = Number(roundedValue) % 10 === 0; // == 0, 10, 20, 50...

      return isEndsWithZero ? roundedValue.replace('.0', '') : roundedValue;
    }

    if (typeof value === 'boolean') {
      if (CUSTOM_FEATURE_NAME[featureKey]) {
        return value === true ? CUSTOM_FEATURE_NAME[featureKey].truthy : CUSTOM_FEATURE_NAME[featureKey].falsy;
      }

      return value === true ? 'Yes' : 'No';
    }

    return '-';
  };

  static formatUnit = (unit: string): string => {
    if (!unit) return '';

    const ingored = ['boolean', 'time_delta'];
    if (ingored.some(char => char === unit)) {
      return '';
    }

    const withoutSpace = ['%', 'x'];
    if (withoutSpace.some(char => char === unit)) {
      return unit;
    }

    return ` ${unit}`;
  };

  static formatRawData = (value: number | boolean | string, unitType = '', featureKey?: string): string => {
    const score = TableUtils.formatScore(value, unitType, featureKey);
    const unit = TableUtils.formatUnit(unitType);

    return score + unit;
  };

  static isMaxValue = (currentValue: number | boolean, allRawValues: number[] | boolean[]): boolean => {
    if (typeof currentValue === 'boolean') return currentValue;

    const maxValue = Math.max(...(allRawValues as number[]));

    if (maxValue === 0) return false;

    return currentValue === maxValue;
  };

  static isMinValue = (currentValue: number | boolean, allRawValues: number[] | boolean[]): boolean => {
    if (typeof currentValue === 'boolean') return !currentValue;

    const minValue = Math.min(...(allRawValues as number[]));

    return currentValue === minValue;
  };

  // 2.33 == 2h 20m
  static convertDecimalHoursIntoTime = (decimalHours: number): string => {
    let hours = Math.trunc(decimalHours);

    const decimalMinutes = decimalHours % 1;

    // rounding minutes to get neat numbers in some cases, e.g. 2.33 == 2h 20m instead of 2h 19m
    let minutes = Math.round(decimalMinutes * 60);

    // since we're rounding, 59 can be converted to 60...
    if (minutes === 60) {
      hours += 1;
      minutes = 0;
    }

    let time = '';
    if (hours > 0) time += `${hours} hour(s)`;
    if (minutes > 0) {
      const space = time ? ' ' : '';
      time += `${space}${minutes} min(s)`;
    }

    return time || '0';
  };

  static hasActiveRedFlag = (category: CompetitionItemResponseType, score: number): boolean => {
    return 'red_flag' in category && score === 0;
  };

  static countNumberOfActiveRedFlags = (
    categories: CompetitionMainCategoryResponseType[],
    scores: CompetitionScoresResponseType
  ): number => {
    let count = 0;
    categories.forEach(category => {
      category.sub_sections.forEach(subCategory => {
        subCategory.sub_sections.forEach(dataFeature => {
          const hasFlag = TableUtils.hasActiveRedFlag(dataFeature, scores[dataFeature.key]);
          if (hasFlag) count += 1;
        });
      });
    });

    return count;
  };

  static buildTotalScoresRows = (
    scores: CompetitionScoresResponseType[],
    categories: CompetitionMainCategoryResponseType[]
  ): { title: string; sourceValues: number[]; formatted: (number | string)[] }[] => {
    const total = scores.map(score => score.total);
    const architectureProgramme = scores.map(score => score.total_program);
    const archilyse = scores.map(score => score.total_archilyse);
    const numberOfRedFlags = scores.map(score => TableUtils.countNumberOfActiveRedFlags(categories, score));

    return [
      { title: 'Gesamtpunktzahl', sourceValues: total, formatted: total.map(score => TableUtils.formatScore(score)) },
      {
        title: 'Auswertung aller Items (exklusive Archilyse-spezifische Items)',
        sourceValues: architectureProgramme,
        formatted: architectureProgramme.map(score => TableUtils.formatScore(score)),
      },
      {
        title: 'Auswertung aller Archilyse-spezifischen Items',
        sourceValues: archilyse,
        formatted: archilyse.map(score => TableUtils.formatScore(score)),
      },
      { title: 'Anzahl Red Flags', sourceValues: numberOfRedFlags, formatted: numberOfRedFlags },
    ];
  };

  static buildTotalPricesRows = (
    scores: CompetitionScoresResponseType[],
    competitorsUnits: CompetitorsUnitsResponse[],
    currency: string,
    prices_are_rent: boolean
  ): { title: string; sourceValues: number[]; formatted: string[] }[] => {
    const orderedUnits = TableUtils.orderCompetitorUnitsByScore(scores, competitorsUnits);
    const units = orderedUnits.filter(Boolean).map(({ units }) => units);

    const total = units.map(unit => PriceUtils.computeTotalPrice(unit));
    const min = units.map(unit => PriceUtils.findMinPricePerM2(unit));
    const mean = units.map(unit => PriceUtils.findMeanPricePerM2(unit));
    const max = units.map(unit => PriceUtils.findMaxPricePerM2(unit));
    return [
      {
        title: prices_are_rent ? 'Gesamtbruttomiete / Jahr' : 'Gesamtertrag Verkauf',
        sourceValues: total,
        formatted: scores.map((_, index) =>
          PriceUtils.formatPrice(total[index], { style: 'currency', currency: currency })
        ),
      },
      {
        title: 'Min. Ertrag / m²',
        sourceValues: min,
        formatted: scores.map((_, index) => PriceUtils.formatPricePerM2(min[index], currency)),
      },
      {
        title: 'Durchschnittlicher Ertrag / m²',
        sourceValues: mean,
        formatted: scores.map((_, index) => PriceUtils.formatPricePerM2(mean[index], currency)),
      },
      {
        title: 'Max. Ertrag / m²',
        sourceValues: max,
        formatted: scores.map((_, index) => PriceUtils.formatPricePerM2(max[index], currency)),
      },
    ];
  };
}

export default TableUtils;
