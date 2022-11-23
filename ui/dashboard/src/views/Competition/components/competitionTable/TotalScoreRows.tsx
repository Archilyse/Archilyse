import React from 'react';
import { Icon } from 'archilyse-ui-components';
import cn from 'classnames';
import { CompetitionMainCategoryResponseType, CompetitionScoresResponseType } from '../../../../common/types';
import CompetitionTooltip from '../CompetitionTooltip';
import Expandable from '../Expandable';
import Row from './Row';
import TableUtils from './TableUtils';

const ROBOT_ICON_STYLE = {
  width: 18,
  height: 18,
  marginLeft: 0,
  fill: '#757575',
};

type Props = {
  categories: CompetitionMainCategoryResponseType[];
  scores: CompetitionScoresResponseType[];
};

const TotalScoreRows = ({ scores, categories }: Props): JSX.Element => {
  const [total, architectureProgramme, archilyse, numberOfRedFlags] = TableUtils.buildTotalScoresRows(
    scores,
    categories
  );

  const totalScoreRow = { id: 'total_score', title: total.title, scores: total.formatted };
  const expandedScores = [
    {
      id: 'architecture_programme_score',
      title: architectureProgramme.title,
      scores: architectureProgramme.formatted,
    },
    {
      id: 'archilyse_score',
      title: (
        <div className="expandable-field">
          {archilyse.title}
          <div className="icons-container">
            <CompetitionTooltip title="Dieses Item ist von Archilyse automatisiert">
              <span role="img" aria-label="automatized item">
                <Icon style={ROBOT_ICON_STYLE}>robot</Icon>
              </span>
            </CompetitionTooltip>
          </div>
        </div>
      ),
      scores: archilyse.formatted,
    },
  ];

  return (
    <Row
      id={totalScoreRow.id}
      values={scores}
      getCellValue={(_, index) => total.sourceValues[index]}
      getRowValues={() => total.sourceValues}
      renderLabel={expandedProps => (
        <td className="cell field">
          <Expandable {...expandedProps}>{total.title}</Expandable>
        </td>
      )}
      renderCell={(_, index, className) => (
        <td key={index} className={className}>
          {total.formatted[index]}
        </td>
      )}
    >
      {expandedScores.map(({ id, title, scores: _scores }) => (
        <Row
          key={id}
          id={`${totalScoreRow.id}.${id}`}
          values={_scores}
          getCellValue={score => Number(score)}
          getRowValues={() => (_scores as string[]).map(Number)}
          renderLabel={() => <td className="cell field subfield">{title}</td>}
          renderCell={(score, index, className) => (
            <td key={index} className={cn(className, 'subfield price')}>
              {score}
            </td>
          )}
        />
      ))}
      <Row
        id={`${totalScoreRow.id}.red_flags_number`}
        values={numberOfRedFlags.sourceValues}
        getCellValue={value => value}
        getRowValues={() => numberOfRedFlags.sourceValues}
        renderLabel={() => <td className="cell field subfield">Anzahl Red Flags</td>}
        renderCell={(number, index) => {
          const isMinumum = TableUtils.isMinValue(number, numberOfRedFlags.sourceValues);

          return (
            <td key={index} className={cn('cell subfield price', { bold: isMinumum })}>
              {number}
            </td>
          );
        }}
      />
    </Row>
  );
};

export default TotalScoreRows;
