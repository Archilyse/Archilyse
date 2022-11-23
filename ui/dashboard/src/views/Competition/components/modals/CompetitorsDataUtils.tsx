import React from 'react';
import {
  CompetitionMainCategoryResponseType,
  CompetitorClientInput,
  CompetitorResponseType,
} from '../../../../common/types';
import { ColumnType, RowOptionType, RowType } from '../../../../components/EditableTable/EditableTable';
import { ROW_OPTION_BY_CATEGORY, UploadedFeaturesBaseRows } from './competitorsDataRows';

class CompetitorsDataUtils {
  static getFixedRows = (
    uploadedFeatures: UploadedFeaturesBaseRows[],
    competitorsData: CompetitorClientInput[]
  ): RowType[] => {
    return uploadedFeatures.map((row: RowType) => {
      const data = competitorsData.reduce(
        (acc, item) => ({ ...acc, [item.competitor_id]: item.features[row.item.key] }),
        {}
      );

      return {
        ...row,
        ...data,
        item: <span className="upload-raw-data-item-cell">{row.item.value}</span>,
      };
    });
  };

  static getRowsOptions = (uploadedFeatures: UploadedFeaturesBaseRows[]): RowOptionType[] => {
    return uploadedFeatures.map(feature => ROW_OPTION_BY_CATEGORY[feature.item.key]);
  };

  static getFixedColumns = (competitors: CompetitorResponseType[]): ColumnType[] => {
    const fixed = [
      {
        header: 'Subcategory',
        field: 'subcategory',
        editable: false,
        editableHeader: false,
      },
      {
        header: 'Item',
        field: 'item',
        editable: false,
        editableHeader: false,
      },
    ];

    return [
      ...fixed,
      ...competitors.map(competitor => ({
        header: competitor.name,
        field: String(competitor.id),
        editable: true,
        editableHeader: false,
      })),
    ];
  };

  static processRows = (
    uploadedFeatures: UploadedFeaturesBaseRows[],
    rows: RowType[],
    competitors: CompetitorResponseType[]
  ): Record<number, number | boolean> => {
    const processedRows = {};
    competitors.forEach(competitor => {
      const fields = CompetitorsDataUtils._generateFields(uploadedFeatures, rows, competitor);
      const hasValues = Object.keys(fields).length > 0;

      if (hasValues) Object.assign(processedRows, { [competitor.id]: fields });
    });

    return processedRows;
  };

  static _processValue = (value: string): number | boolean => {
    if (value === 'true') return true;
    if (value === 'false') return false;
    if (typeof value === 'boolean') return value;

    return Number(value);
  };

  static findUploadedFeatures = (categories: CompetitionMainCategoryResponseType[]): UploadedFeaturesBaseRows[] => {
    const uploadedFeatures = categories.reduce((features: UploadedFeaturesBaseRows[], category) => {
      category.sub_sections.forEach(subCategory => {
        subCategory.sub_sections.forEach(dataFeature => {
          if (dataFeature.uploaded) {
            features.push({
              subcategory: subCategory.name,
              item: { key: dataFeature.key, value: dataFeature.name },
            });
          }
        });
      });

      return features;
    }, []);

    return uploadedFeatures;
  };

  static _generateFields(
    uploadedFeatures: UploadedFeaturesBaseRows[],
    rows: RowType[],
    competitor: CompetitorResponseType
  ): RowType {
    return uploadedFeatures.reduce((acc, fixedRow, index) => {
      const value = rows[index][competitor.id];
      if (value === undefined || value === null) return acc;

      return { ...acc, [fixedRow.item.key]: this._processValue(value) };
    }, {});
  }
}

export default CompetitorsDataUtils;
