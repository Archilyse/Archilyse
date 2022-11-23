/**
 * Translation from a dictionary to an array
 * @param dictFloors
 */
export function floorsToArray(dictFloors) {
  const floors = [];
  for (const floorId in dictFloors) {
    if (dictFloors.hasOwnProperty(floorId)) {
      floors.push(dictFloors[floorId]);
    }
  }
  return floors;
}

/**
 * Return the ordinal
 * @param n
 */
export function nth(n) {
  return ['st', 'nd', 'rd'][((((n + 90) % 100) - 10) % 10) - 1] || 'th';
}

/**
 * We display a floor
 * @param floorNr
 */
export function floorToHumanStr(floorNr): string {
  if (floorNr === 0) {
    return 'Ground floor';
  }
  if (floorNr > 0) {
    return `${floorNr}${nth(floorNr)} floor`;
  }
  if (floorNr < 0) {
    return `${floorNr} UG`;
  }
  // When provided a string
  return floorNr;
}

/**
 * Given an array of floors, we return a set of ranges of floors.
 * @param floorArray
 */
export function getRangesHuman(floorArray) {
  const ranges = [];
  let floorRangeStart;
  let floorRangeEnd;

  const orderedFloors = floorArray.sort((floorA, floorB) => floorA - floorB);
  for (let i = 0; i < orderedFloors.length; i += 1) {
    let currentFloor = orderedFloors[i];
    let nextFloor = orderedFloors[i + 1];
    let areFloorsSequential = nextFloor - currentFloor === 1;

    floorRangeStart = currentFloor;
    floorRangeEnd = currentFloor;

    // We iterate until we find the end of the range
    while (areFloorsSequential) {
      floorRangeEnd = nextFloor;
      i += 1;

      currentFloor = orderedFloors[i];
      nextFloor = orderedFloors[i + 1];
      areFloorsSequential = nextFloor - currentFloor === 1;
    }

    addHumanRange(ranges, floorRangeStart, floorRangeEnd);
  }
  return ranges;
}

/**
 * Transforms the range into a string and add it to the array of ranges.
 * @param ranges Should be initialized
 * @param rangeStart
 * @param rangeEnd
 */
function addHumanRange(ranges, rangeStart, rangeEnd) {
  if (rangeStart === rangeEnd) {
    ranges.push(`${floorToHumanStr(rangeStart)}`);
  } else if (rangeStart === rangeEnd + 1) {
    ranges.push(`${floorToHumanStr(rangeStart)}`);
    ranges.push(`${floorToHumanStr(rangeEnd)}`);
  } else {
    ranges.push(`${floorToHumanStr(rangeStart)} to ${floorToHumanStr(rangeEnd)}`);
  }
}

/**
 * We build a structure to be displayed in the floor dropdown
 * @param floors
 */
export function buildFloorArrayToDisplay(floors) {
  const objFloorsToDisplay = groupFloorsInRanges(floors);

  return Object.keys(objFloorsToDisplay).map(plan_id => {
    const floors = objFloorsToDisplay[plan_id];
    const floor_number = floors.map(f => f.floor_number).sort();
    const floor_numbers = getRangesHuman(floor_number).join(', ');
    return {
      plan_id,
      floor_numbers,
    };
  });
}

/**
 * We group the floors by plan id
 * @param floors
 */
export function groupFloorsInRanges(floors) {
  return floors.reduce((r, f) => {
    r[f.plan_id] = r[f.plan_id] || [];
    r[f.plan_id].push(f);
    return r;
  }, Object.create(null));
}
