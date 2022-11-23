import { Dropdown, HeatmapModalContent } from 'archilyse-ui-components';
import React, { useState } from 'react';
import {
  CompetitionItemResponseType,
  CompetitionMainCategoryResponseType,
  CompetitionSubSectionResponseType,
  CompetitorResponseType,
} from '../../../../common/types';
import SIMULATION_NAME_BY_DATA_FEATURE from './simulationNameByDataFeature';
import './competitionHeatmapsModal.scss';

type Props = {
  category: CompetitionMainCategoryResponseType | CompetitionSubSectionResponseType | CompetitionItemResponseType;
  competitors: CompetitorResponseType[];
  onClose: () => void;
};

const CompetitionHeatmapsModal = ({ category, competitors, onClose }: Props) => {
  const [competitor, setCompetitor] = useState(competitors[0].id);
  const [selected, setSelected] = useState({ building: null, floor: null });

  const handleCompetitorChange = event => {
    setCompetitor(event.target.value);
    setSelected({ building: null, floor: null });
  };

  const competitorsOptions = competitors.map(_c => ({
    label: _c.name,
    value: _c.id,
  }));

  return (
    <HeatmapModalContent
      header={category.name}
      siteId={competitor}
      selectedByDefault={{ dimension: SIMULATION_NAME_BY_DATA_FEATURE[category.key], ...selected }}
      extraLeftFilters={
        <Dropdown
          value={competitor || ''}
          options={competitorsOptions}
          onChange={handleCompetitorChange}
          className="heatmap-list dimensions-dropdown"
        />
      }
      onClose={onClose}
    />
  );
};

export default CompetitionHeatmapsModal;
