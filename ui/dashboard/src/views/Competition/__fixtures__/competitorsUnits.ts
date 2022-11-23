import { CompetitorsUnitsResponse } from '../../../common/types';

const competitorsUnits: CompetitorsUnitsResponse[] = [
  {
    competitor_id: 1,
    units: [
      { id: 1, ph_gross_price: 10, net_area: 2 },
      { id: 1, ph_gross_price: 20, net_area: 4 },
      { id: 1, ph_gross_price: 30, net_area: 6 },
      { id: 1, ph_gross_price: 40, net_area: 10 },
    ],
  },
  {
    competitor_id: 2,
    units: [
      { id: 1, ph_gross_price: 100, net_area: 5 },
      { id: 1, ph_gross_price: 200, net_area: 6 },
      { id: 1, ph_gross_price: 300, net_area: 50 },
      { id: 1, ph_gross_price: 400, net_area: 40 },
    ],
  },
];

export default competitorsUnits;
