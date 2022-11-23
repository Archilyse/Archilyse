import { AreaRequirements } from 'Components/CompetitionConfigView/AreaRequirements';
import React from 'react';

export function MinBathroomSizes(props) {
  return (
    <AreaRequirements
      names={{
        smallSideName: 'min_bathroom_sizes.min_small_side',
        bigSideName: 'min_bathroom_sizes.min_big_side',
        areaName: 'min_bathroom_sizes.min_area',
      }}
      {...props}
    />
  );
}
