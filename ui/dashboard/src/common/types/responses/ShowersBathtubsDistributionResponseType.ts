import FlatDeviationResponseType from './FlatDeviationResponseType';

type ShowersBathtubsDistributionResponseType = {
  showers: number;
  bathtubs: number;
  basins: number;
} & FlatDeviationResponseType;

export default ShowersBathtubsDistributionResponseType;
