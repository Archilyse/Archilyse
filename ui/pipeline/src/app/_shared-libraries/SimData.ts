import * as d3 from 'd3';

/** Coordinates constants to index point arrays */
/** X coordinate - 0 */
export const COOR_X = 0;
/** Y coordinate - 1 */
export const COOR_Y = 1;

/** Default color set for simulations */
export const colors = [
  '#2c7bb6',
  '#00a6ca',
  '#00ccbc',
  '#90eb9d',
  '#ffff8c',
  '#f9d057',
  '#f29e2e',
  '#e76818',
  '#d7191c',
];

/**
 * The Hexagons with this value are not displayed or taken into consideration
 * @type {number}
 */
export const EXCLUDED_NUMBER = -666;

/**
 * We make the data matrix flat.
 * We get the color function with the min max
 * We get the values to display the legend
 * @param dataArray
 * @param min
 * @param max
 * @param numSteps
 */
export function getHexColorsAndLegend(dataArray, min, max, numSteps = 30) {
  const flatArray = [].concat.apply([], dataArray);
  const numberToHex = getNumberToHexFunction(min, max);
  const hexColors = flatArray.map(el => numberToHex(el));

  const numDecimals = 1;

  const legend = {};
  const range = max - min;

  for (let i = 0; i < numSteps; i += 1) {
    const rawVal = min + (range * i) / numSteps;

    const value = rawVal.toFixed(numDecimals);
    legend[value] = numberToHex(rawVal);
  }

  return {
    hexColors,
    legend,
    max,
    min,
  };
}

/**
 * Information provided in Klux, so when the unit is lux we multiply by 10;
 * @param unit
 */
export function correctScale(unit: string) {
  return unit === 'lux' || unit === 'Lux' ? 1000 : 1;
}

/**
 * returns the function that transforms a number in the range to a color
 * @param min
 * @param max
 * @returns {(v) => (string | any)}
 */
export function getNumberToHexFunction(min, max) {
  const domain = [];

  const grad = colors.length;
  for (let i = 0; i < grad; i += 1) {
    domain.push((i / grad) * max);
  }
  const corrColor = d3.scaleLinear().domain(domain).range(colors);
  return v => {
    if (v === EXCLUDED_NUMBER) {
      return 'rgba(255,255,255,0)';
    }
    return corrColor(v);
  };
}

/**
 * Returns
 * @param polygonJson
 */
export function polygonJsonCoordinatesStandard(polygonJson) {
  if (polygonJson.type === 'Polygon') {
    return [polygonJson.coordinates];
  }

  if (polygonJson.type === 'MultiPolygon') {
    return polygonJson.coordinates;
  }
  console.error('Object is not a Polygon or a MultiPolygon', polygonJson);
}

/**
 * Returns the bounding box out of a polygon or a MultiPolygon
 * Raises an error if the type is wrong
 * @param polygonJson
 */
export function polygonJsonBoundingBox(polygonJson) {
  if (polygonJson.type === 'Polygon') {
    return svgBoundingBox(polygonJson.coordinates);
  }

  if (polygonJson.type === 'MultiPolygon') {
    let result = null;
    for (let i = 0; i < polygonJson.coordinates.length; i += 1) {
      const polygon = polygonJson.coordinates[i];
      const currentResult = svgBoundingBox(polygon);
      if (result === null) {
        result = currentResult;
      } else {
        result.x1 = currentResult.x1 < result.x1 ? currentResult.x1 : result.x1;
        result.x2 = currentResult.x2 > result.x2 ? currentResult.x2 : result.x2;
        result.y1 = currentResult.y1 < result.y1 ? currentResult.y1 : result.y1;
        result.y2 = currentResult.y2 > result.y2 ? currentResult.y2 : result.y2;
      }
    }
    return result;
  }
  console.error('Object is not a Polygon or a MultiPolygon', polygonJson);
}

/**
 * We get the bounding box out of a svg polygon
 * @param polygonVertices
 */
export function svgBoundingBox(polygonVertices) {
  // Here we calculate the bounding box
  let boxX1 = null;
  let boxX2 = null;
  let boxY1 = null;
  let boxY2 = null;
  polygonVertices.map(polygonVerticesRows => {
    polygonVerticesRows.map(polygonVertice => {
      const x = polygonVertice[COOR_X];
      const y = polygonVertice[COOR_Y];

      if (boxX1 === null) {
        boxX1 = x;
        boxX2 = x;
        boxY1 = y;
        boxY2 = y;
      } else {
        if (x < boxX1) {
          boxX1 = x;
        }
        if (x > boxX2) {
          boxX2 = x;
        }
        if (y < boxY1) {
          boxY1 = y;
        }
        if (y > boxY2) {
          boxY2 = y;
        }
      }
    });
  });

  return {
    x1: boxX1,
    x2: boxX2,
    y1: boxY1,
    y2: boxY2,
  };
}

/**
 * Descriptions that explain the simulations
 * @param simulationName
 */
export function getSimulationDescription(simulationName: string) {
  if (simulationName === 'isovist') {
    return {
      title: 'Isovist simulation',
      body:
        '<p>This simulations represents the amount of volume in m<sup>3</sup> seen from each point in the simulation.</p>' +
        '<p>The simulation was run on a 0.5x0.5m grid in each room whereby points closer than 0.1m to walls were neglected.</p>',
      image: null,
    };
  }

  if (simulationName.substr(0, 4) === 'sun-') {
    return {
      title: 'Real view: Sun information.',
      body:
        '<p>The sun simulation evaluates the expected direct illuminance of a given point ' +
        'and is measured in lux at a given time.' +
        ' The simulation was executed on a 0.5x0.5m grid (minimum 0.1m distance to walls).</p>' +
        '<p>The simulations was performed for the days of summer solstice, winter solstice and vernal equinox.</p> ' +
        '<p>To evaluate different conditions throughout a day, it was performed for 2h after sunrise (morning), ' +
        '2h before sunset (evening) and the apex in the sun’s motion (noon). </p>',
      image: null,
    };
  }

  return {
    title: 'Real view: Standard information.',
    body: `This simulations represents the amount of visible ${simulationName} from inside each part of the current building. The values are expressed in steradians (ranging from 0 to 4PI)
    and represent the amount a certain object category occupies in the spherical field of view.`,
    image: null,
  };
}
