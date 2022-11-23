import React from 'react';
import { Navbar } from 'archilyse-ui-components';
import { useHistory } from 'react-router-dom';
import { Drawer } from '../../components';
import { C } from '../../common';
import { CompetitionType } from '../../common/types';
import useFetchData from './useFetchData';
import './competitions.scss';

type GridProps = {
  items: CompetitionType[];
  onClickCard: (competition: CompetitionType) => void;
};

const Grid = ({ items, onClickCard }: GridProps) => {
  return (
    <div className="grid">
      {items.map(competition => (
        <div key={competition.id || competition.name} className="column card" onClick={() => onClickCard(competition)}>
          <h1>{competition.name}</h1>
        </div>
      ))}
    </div>
  );
};

const Competitions = () => {
  const { competitions, clientName } = useFetchData();
  const history = useHistory();

  const onClickCompetitionCard = competition => {
    history.push(C.URLS.COMPETITION(competition.id));
  };

  return (
    <div className="competitions">
      <div className="list-drawer">
        <Drawer open={true}>
          <div className="user">
            <div className="account-icon" />
            <p>{clientName}</p>
          </div>
        </Drawer>
      </div>
      <div className="main-content">
        <Navbar logoRedirect={C.URLS.COMPETITIONS()} />
        <div className="header">
          <h1></h1>
        </div>
        <Grid items={competitions} onClickCard={onClickCompetitionCard} />
      </div>
      <footer className="global-footer">&copy; Copyright 2021 Archilyse. All rights reserved.</footer>
    </div>
  );
};

export default Competitions;
