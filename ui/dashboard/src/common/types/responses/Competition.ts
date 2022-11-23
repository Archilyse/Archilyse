import CompetitionWeightsResponseType from './CompetitionWeightsResponseType';

type CompetitionType = {
  id?: number;
  name: string;
  configuration_parameters: Record<string, any>;
  weights: CompetitionWeightsResponseType;
  currency: string;
  prices_are_rent: boolean;
};

export default CompetitionType;
