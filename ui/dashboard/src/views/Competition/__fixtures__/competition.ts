import { CompetitionType } from '../../../common/types';

const competition: CompetitionType = {
  name: 'Competition name',
  configuration_parameters: {},
  weights: {
    architecture_room_programme: 0.25,
    architecture_usage: 0.4,
    environmental: 0.25,
    further_key_figures: 0.1,
  },
  currency: 'CHF',
  prices_are_rent: true,
};

export default competition;
