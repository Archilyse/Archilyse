import React from 'react';
import cn from 'classnames';
import { CompetitionScoresResponseType, CompetitorsUnitsResponse } from '../../../../common/types';
import Expandable from '../Expandable';
import Row from './Row';
import TableUtils from './TableUtils';

type Props = {
  scores: CompetitionScoresResponseType[];
  competitorsUnits: CompetitorsUnitsResponse[];
  currency: string;
  prices_are_rent: boolean;
};

const TotalPricesRows = ({ scores, competitorsUnits, currency, prices_are_rent }: Props): JSX.Element => {
  const [total, min, mean, max] = TableUtils.buildTotalPricesRows(scores, competitorsUnits, currency, prices_are_rent);

  const totalPriceRow = {
    id: 'total_price',
    title: total.title,
    prices: total.sourceValues,
    formatted: total.formatted,
  };
  const expandedPrices = [
    { id: 'min_price', title: min.title, prices: min.sourceValues, formatted: min.formatted },
    { id: 'mean_price', title: mean.title, prices: mean.sourceValues, formatted: mean.formatted },
    { id: 'max_price', title: max.title, prices: max.sourceValues, formatted: max.formatted },
  ];

  return (
    <Row
      id={totalPriceRow.id}
      values={scores}
      getCellValue={(_, index) => totalPriceRow.prices[index]}
      getRowValues={() => totalPriceRow.prices}
      renderLabel={expandedProps => (
        <td className="cell field" id="total-price-id">
          <Expandable {...expandedProps}>{totalPriceRow.title}</Expandable>
        </td>
      )}
      renderCell={(_, index, className) => (
        <td key={index} className={cn(className, 'price')} title={totalPriceRow.formatted[index]}>
          {totalPriceRow.formatted[index]}
        </td>
      )}
    >
      {expandedPrices.map(({ id, title, prices, formatted }) => (
        <Row
          id={`${totalPriceRow.id}.${id}`}
          key={id}
          values={scores}
          getCellValue={(_, index) => prices[index]}
          getRowValues={() => prices}
          renderLabel={() => <td className="cell field subfield">{title}</td>}
          renderCell={(_, index, className) => (
            <td key={index} className={cn(className, 'subfield price')} title={formatted[index]}>
              {formatted[index]}
            </td>
          )}
        />
      ))}
    </Row>
  );
};

export default TotalPricesRows;
