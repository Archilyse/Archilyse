import React, { useEffect, useState } from 'react';
import { Navbar, RequestStatus } from 'archilyse-ui-components';
import { useParams } from 'react-router-dom';
import { C } from '../../common';
import Sidebar from './Sidebar';
import Expandable from './components/Expandable';
import useFetchData from './useFetchData';
import Content from './Content';
import SpreadsheetUtils from './modules/SpreadsheetUtils';
import './competition.scss';

const getNavbarLinks = (competitionId: string, competitionName) => [
  { url: C.URLS.COMPETITIONS(), label: 'Wettbewerbe' },
  { url: C.URLS.COMPETITION(competitionId), label: competitionName || 'Wettbewerb ...' },
];

const Competition = (): JSX.Element => {
  const { id: competitionId } = useParams<{ id: string }>();
  const { state, actions } = useFetchData(competitionId);
  const { categories, competitors, competitorsUnits, competition, scores } = state;

  const [expandedCategories, setExpandedCategories] = useState<string[]>([]);

  const handleCompetitorsUpload = () => {
    Promise.all([actions.updateCompetitors(), actions.updateScores()]);
  };

  const onExportExcel = () => {
    const rows = SpreadsheetUtils.buildAllRows(
      categories.data,
      scores.data,
      competitors.data,
      competitorsUnits.data,
      competition.data?.currency,
      competition.data?.prices_are_rent
    );
    SpreadsheetUtils.download(rows);
  };

  useEffect(() => {
    document.title = 'Wettbewerbsvorprüfung | Archilyse';
  }, []);

  const canExport =
    categories.status === RequestStatus.FULFILLED &&
    scores.status === RequestStatus.FULFILLED &&
    competitors.status === RequestStatus.FULFILLED &&
    competitorsUnits.status === RequestStatus.FULFILLED;

  return (
    <Expandable.Provider value={{ expandedCategories, onExpand: setExpandedCategories }}>
      <div className="competition-tool">
        <Sidebar
          categories={categories}
          weights={competition.data?.weights}
          competitors={competitors.data}
          onSaveWeights={actions.saveWeights}
          onCompetitorsDataUpload={handleCompetitorsUpload}
          onExportExcel={canExport ? onExportExcel : () => null}
        />

        <main>
          <Navbar links={getNavbarLinks(competitionId, competition.data?.name)} logoRedirect={C.URLS.COMPETITIONS()} />
          <header>
            <div className="title">
              <h1>Gesamtübersicht</h1>
            </div>
            <p>{competition.data?.name}</p>
          </header>

          <Content
            scores={scores}
            competitors={competitors.data}
            competitorsUnits={competitorsUnits.data}
            categories={categories.data}
            currency={competition.data?.currency}
            prices_are_rent={competition.data?.prices_are_rent}
          />
        </main>
      </div>
    </Expandable.Provider>
  );
};

export default Competition;
