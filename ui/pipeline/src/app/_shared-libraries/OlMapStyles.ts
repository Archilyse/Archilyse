import OlStyle from 'ol/style/Style';
import OlStyleFill from 'ol/style/Fill';
import OlStyleStroke from 'ol/style/Stroke';

/** Map style definition, default footprint */
export const styleNormal = new OlStyle({
  fill: new OlStyleFill({
    color: 'rgba(255, 255, 255, 0.6)',
  }),
  stroke: new OlStyleStroke({
    color: '#5a5a5a',
  }),
});

/** Map style definition, mouse over footprint */
export const styleOver = new OlStyle({
  fill: new OlStyleFill({
    color: 'rgba(200, 200, 200, 0.6)',
  }),
  stroke: new OlStyleStroke({
    color: '#dddddd',
    width: 2,
  }),
});
