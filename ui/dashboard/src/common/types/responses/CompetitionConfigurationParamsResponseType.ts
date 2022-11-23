import { FlatDeviationResponseType } from '..';
import ShowersBathtubsDistributionResponseType from './ShowersBathtubsDistributionResponseType';

type CompetitionConfigurationParamsResponseType = {
  flat_types_distribution: FlatDeviationResponseType[];
  showers_bathtubs_distribution: ShowersBathtubsDistributionResponseType[];
};

export default CompetitionConfigurationParamsResponseType;
