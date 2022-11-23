export const simulation = {
  id: 1,
  created: '2021-04-09T10:28:20.506549',
  floor_number: 1,
  lat: 47.37462,
  lon: 8.528688,
  type: 'view',
  result: {
    obesrvation_points: [
      { lat: 47.37462, lon: 8.528688, height: 413.5 },
      { lat: 47.37464, lon: 8.52869, height: 413.5 },
      { lat: 47.37466, lon: 8.528692, height: 413.5 },
      { lat: 47.37468, lon: 8.528694, height: 413.5 },
    ],
    buildings: [1, 2, 3, 4],
  },
};

export const simulationWithError = {
  id: 1,
  created: '2021-04-09T10:28:20.506549',
  floor_number: 1,
  lat: 47.3746231865988,
  lon: 8.52868889932289,
  type: 'view',
  result: {
    msg: "You provided incorrect location so we couldn't simulate anything",
    code: 'IncorrectLocationException',
  },
};
