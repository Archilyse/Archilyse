import { AreaRequirements } from 'Components/CompetitionConfigView/AreaRequirements';
import React from 'react';

export function MinimumRoomSizes(props) {
  return (
    <>
      <AreaRequirements
        names={{
          smallSideName: 'min_room_sizes.big_room_side_small',
          bigSideName: 'min_room_sizes.big_room_side_big',
          areaName: 'min_room_sizes.big_room_area',
        }}
        label="Big Room"
        {...props}
      />
      <AreaRequirements
        names={{
          smallSideName: 'min_room_sizes.small_room_side_small',
          bigSideName: 'min_room_sizes.small_room_side_big',
          areaName: 'min_room_sizes.small_room_area',
        }}
        label="Small Room"
        {...props}
      />
    </>
  );
}
