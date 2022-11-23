import React from 'react';
import cn from 'classnames';
import { Icon } from 'archilyse-ui-components';
import './competitionTable.scss';
import {
  CompetitionItemResponseType,
  CompetitionMainCategoryResponseType,
  CompetitionScoresResponseType,
  CompetitionSubSectionResponseType,
  CompetitorResponseType,
  CompetitorsUnitsResponse,
} from '../../../../common/types';
import { Info } from '../../../../components';
import CompetitionTooltip from '../CompetitionTooltip';
import SIMULATION_NAME_BY_DATA_FEATURE from '../modals/simulationNameByDataFeature';
import ButtonWithModal from '../modals/ButtonWithModal';
import Expandable from '../Expandable';
import CompetitionHeatmapsModal from '../modals/CompetitionHeatmapsModal';
import TotalScoreRows from './TotalScoreRows';
import TotalPricesRows from './TotalPricesRows';
import TableUtils from './TableUtils';
import Flag from './Flag';
import WithSuffix from './WithSuffix';
import Row from './Row';

export type CompetitionTableProps = {
  competitors: CompetitorResponseType[];
  competitorsUnits: CompetitorsUnitsResponse[];
  scores: CompetitionScoresResponseType[];
  categories: CompetitionMainCategoryResponseType[];
  currency: string;
  prices_are_rent: boolean;
};

const INFO_ICON_SIZE = 16;
const ROBOT_ICON_STYLE = {
  width: 18,
  height: 18,
  marginLeft: 0,
  fill: '#757575',
};

const CompetitionTable = ({
  competitors,
  scores,
  categories,
  competitorsUnits,
  currency,
  prices_are_rent,
}: CompetitionTableProps): JSX.Element => {
  const getIcons = (
    category: CompetitionMainCategoryResponseType | CompetitionSubSectionResponseType | CompetitionItemResponseType
  ) => {
    const icons: React.ReactNode[] = [];

    if (!category) {
      return [];
    }

    if ('info' in category) {
      icons.push(<Info text={category.info} width={INFO_ICON_SIZE} height={INFO_ICON_SIZE} />);
    }

    if ('archilyse' in category && category.archilyse) {
      icons.push(
        <CompetitionTooltip title="Dieses Item ist von Archilyse automatisiert.">
          <span role="img" aria-label="automatized item">
            <Icon style={ROBOT_ICON_STYLE}>robot</Icon>
          </span>
        </CompetitionTooltip>
      );
    }

    return icons;
  };
  const getLabelText = (
    category: CompetitionMainCategoryResponseType | CompetitionSubSectionResponseType | CompetitionItemResponseType
  ) => {
    const text = (
      <>
        {category.name} {'red_flag' in category && <Flag title="Für dieses Item sind Grenzwerte definiert" />}
      </>
    );

    if (SIMULATION_NAME_BY_DATA_FEATURE[category.key]) {
      return (
        <ButtonWithModal label={text} className="data-feature-button-to-modal">
          {({ onClose }) => (
            <CompetitionHeatmapsModal
              category={category}
              competitors={TableUtils.orderCompetitorByScore(scores, competitors)}
              onClose={onClose}
            />
          )}
        </ButtonWithModal>
      );
    }

    return text;
  };

  return (
    <div className="competition-tool-table-container">
      <table className="competition-tool-table">
        <thead>
          <tr>
            <th className="cell field">Teilnehmer</th>
            {scores.map((score, index) => (
              <th key={score.id} className="cell" data-testid={index === 0 ? 'winner' : undefined}>
                {TableUtils.findInCompetitors(score.id, competitors, 'name')}
              </th>
            ))}
          </tr>
          <tr className="ranking">
            <th className="cell field">Platzierung</th>
            {scores.map((score, index) => (
              <th key={score.id} className={cn('cell', { winner: index === 0 })}>
                <WithSuffix>{index + 1}</WithSuffix>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <TotalScoreRows categories={categories} scores={scores} />
          <TotalPricesRows
            competitorsUnits={competitorsUnits}
            scores={scores}
            currency={currency}
            prices_are_rent={prices_are_rent}
          />
          {categories.map(category => (
            <Row
              key={category.key}
              id={category.key}
              values={scores}
              getCellValue={score => score[category.key]}
              getRowValues={() => scores.map(score => score[category.key])}
              renderLabel={expandedProps => (
                <td className="cell field">
                  <Expandable {...expandedProps} icons={getIcons(category)}>
                    <div>{getLabelText(category)}</div>
                  </Expandable>
                </td>
              )}
              renderCell={(score, index, className) => (
                <td key={category.key + index} className={className}>
                  {score[category.key]}
                </td>
              )}
            >
              {category.sub_sections.map(subsection => (
                <Row
                  key={`${category.key}.${subsection.key}`}
                  id={`${category.key}.${subsection.key}`}
                  values={scores}
                  getCellValue={score => score[subsection.key]}
                  getRowValues={() => scores.map(score => score[subsection.key])}
                  renderLabel={expandedProps => (
                    <td className="cell field subfield">
                      <Expandable {...expandedProps} icons={getIcons(subsection)} id={'expand_' + subsection.key}>
                        <div>{getLabelText(subsection)}</div>
                      </Expandable>
                    </td>
                  )}
                  renderCell={(score, index, className) => (
                    <td key={subsection.key + index} className={cn(className, 'subfield')}>
                      {TableUtils.formatScore(score[subsection.key])}
                    </td>
                  )}
                >
                  {subsection.sub_sections.map(dataFeature => (
                    <Row
                      key={`${category.key}.${subsection.key}.${dataFeature.key}`}
                      id={`${category.key}.${subsection.key}.${dataFeature.key}`}
                      values={scores}
                      getCellValue={score => score[dataFeature.key]}
                      getRowValues={() => scores.map(score => score[dataFeature.key])}
                      renderLabel={expandedProps => (
                        <td className="cell field sub-subfield-title">
                          <Expandable {...expandedProps} icons={getIcons(dataFeature)}>
                            <div>{getLabelText(dataFeature)}</div>
                          </Expandable>
                        </td>
                      )}
                      renderCell={(score, index, className) => {
                        const hasRedFlag = TableUtils.hasActiveRedFlag(dataFeature, score[dataFeature.key]);
                        const rawData = TableUtils.findInCompetitors(score.id, competitors, dataFeature.key);
                        const formattedRawData = TableUtils.formatRawData(rawData, dataFeature.unit, dataFeature.key);

                        return (
                          <td key={dataFeature.key + index} className={cn(className, 'subfield sub-subfield')}>
                            <span>{formattedRawData}</span>
                            {hasRedFlag && <Flag title="Schwellenwert nicht eingehalten." color="red" />}
                          </td>
                        );
                      }}
                    />
                  ))}
                </Row>
              ))}
            </Row>
          ))}
        </tbody>
      </table>
    </div>
  );
};
export default CompetitionTable;
