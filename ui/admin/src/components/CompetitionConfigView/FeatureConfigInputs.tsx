import { CommercialUseDesired } from 'Components/CompetitionConfigView/CommercialUseDesired';
import { JanitorStorageSize } from 'Components/CompetitionConfigView/JanitorStorageSize';
import { JanitorOfficeSize } from 'Components/CompetitionConfigView/JanitorOfficeSize';
import { ReduitMinSize } from 'Components/CompetitionConfigView/ReduitMinSize';
import { MinimumRoomSizes } from 'Components/CompetitionConfigView/MinimumRoomSizes';
import { MinBathroomSizes } from 'Components/CompetitionConfigView/MinBathroomSizes';
import { ResidentialRatio } from 'Components/CompetitionConfigView/ResidentialRatio';
import { MinBikeBoxCount } from 'Components/CompetitionConfigView/BikeboxCount';
import { MinCorridorSize } from 'Components/CompetitionConfigView/MinCorridorSize';
import { MinOutdoorSize } from 'Components/CompetitionConfigView/MinOutdoorSize';
import { HNFRequirement } from 'Components/CompetitionConfigView/HNFRequirement';
import { MinimumDiningTableSizes } from 'Components/CompetitionConfigView/MinimumDiningTableSizes';

const featureConfigInputs = {
  RESIDENTIAL_USE: CommercialUseDesired,
  RESIDENTIAL_USE_RATIO: ResidentialRatio,
  APT_RATIO_BATHROOM_MIN_REQUIREMENT: MinBathroomSizes,
  APT_RATIO_BEDROOM_MIN_REQUIREMENT: MinimumRoomSizes,
  JANITOR_STORAGE_MIN_SIZE_REQUIREMENT: JanitorStorageSize,
  JANITOR_OFFICE_MIN_SIZE_REQUIREMENT: JanitorOfficeSize,
  APT_PCT_W_STORAGE: ReduitMinSize,
  BUILDING_BICYCLE_BOXES_QUANTITY_PERFORMANCE: MinBikeBoxCount,
  APT_RATIO_NAVIGABLE_AREAS: MinCorridorSize,
  APT_MIN_OUTDOOR_REQUIREMENT: MinOutdoorSize,
  RESIDENTIAL_TOTAL_HNF_REQ: HNFRequirement,
  APT_SIZE_DINING_TABLE_REQ: MinimumDiningTableSizes,
};

export const FeatureConfigInputs = props => {
  return featureConfigInputs[props.feature]({ ...props.featureProps, onChange: props.onChange });
};
