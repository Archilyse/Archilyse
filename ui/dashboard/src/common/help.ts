/*  For mor languagues we will add more files like: help_de, help_fr... and we will use the correct one depending on user's language */
export default {
  UNIT_VIEW: {
    CHARTS: {
      VIEW:
        'The view simulation calculates the visible amount of sky, greenery, water etc. of a given point. The values are expressed in steradians (ranging from 0 to 4pi) and represent the amount a certain object category occupies in the spherical field of view.',
      SUN:
        'The sun simulation calculates the sun exposures in the selected hours and months. Warmer colors indicate more exposure.',
      // @TODO: Update tooltip talking it with PM/iterating here
      CONNECTIVITY: 'Connectivity calculates the distance from any given point to other points in the unit/floor.',
      NOISE: 'The noise simulation aggregates the street-level noise in the urban setting where the project is located',
    },
  },
  CALIBRATOR: {
    SLIDER:
      'Weight the values for each one of the simulation parameters. The price calculations will be updated based on this rating.',
  },
  QA: {
    TITLE: 'Example.',
    SELECT_SIMULATION: 'Simulation to be displayed.',
    SELECT_BUILDING: 'Building to be displayed.',
    SELECT_FLOOR: 'Floor to be displayed.',
    SELECT_UNIT: 'Unit to be displayed.',
    SELECT_LAYOUT: 'Background map style to be displayed.',
    VALIDATION_NOTES: 'Pressing the button "Save notes" will update the notes for the site',
    QA_COMPLETE:
      'Pressing the button "Validate" means that the heatmaps are Ok and the site is ready to be delivered to the clients.',
  },
};
