import { LoadingIndicator, RequestStatus } from 'archilyse-ui-components';
import React from 'react';
import { CompetitionMainCategoryResponseType } from '../../common/types';
import CompetitionTable, { CompetitionTableProps } from './components/competitionTable/CompetitionTable';
import { CompetitionState } from './useFetchData';
import './content.scss';
import CollapseToggles from './components/collapseToggles/CollapseToggles';

const totalScoreToggle = { label: 'Gesamtpunktzahl', value: 'total_score' };
const totalPricesToggle = { label: 'Gesamtbruttomiete / Jahr', value: 'total_price' };
const formatToggles = (categories: CompetitionMainCategoryResponseType[]) =>
  [totalScoreToggle, totalPricesToggle].concat(
    categories.map(category => ({
      label: category.name,
      value: category.key,
    }))
  );

type Props = {
  scores: CompetitionState['scores'];
} & Omit<CompetitionTableProps, 'scores'>;

const Content = ({
  scores,
  competitors,
  competitorsUnits,
  categories,
  currency,
  prices_are_rent,
}: Props): JSX.Element => {
  const hasScores = scores?.data?.length > 0;
  const hasCompetitors = competitors?.length > 0;
  const hasCategories = categories?.length > 0;

  if (scores.status === RequestStatus.PENDING && !hasScores) {
    return (
      <div className="scores-table-loading">
        <LoadingIndicator />
      </div>
    );
    // to not showing empty table we check for competitors and categories are there
  } else if (hasScores || (scores.status === RequestStatus.FULFILLED && hasCompetitors && hasCategories)) {
    return (
      <>
        <CollapseToggles options={formatToggles(categories)} />
        <CompetitionTable
          scores={scores.data}
          competitors={competitors}
          competitorsUnits={competitorsUnits}
          categories={categories}
          currency={currency}
          prices_are_rent={prices_are_rent}
        />
      </>
    );
  } else if (scores.status === RequestStatus.REJECTED) {
    return (
      <p className="scores-table-not-configured">
        Die Daten für den Wettbewerb sind noch nicht vollständig konfiguriert.{' '}
      </p>
    );
  }

  return null;
};

export default Content;
