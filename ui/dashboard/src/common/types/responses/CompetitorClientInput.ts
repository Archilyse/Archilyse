type CompetitorClientInput = {
  competition_id: number;
  competitor_id: number;
  features: { [key: string]: number | boolean };
  created: string;
  updated: string;
};

export default CompetitorClientInput;
