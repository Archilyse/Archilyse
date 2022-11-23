export class TestingConstants {
  /**
   * Example brooksModel for testing purposes.
   */
  public static brooksModel = {
    basic_features: {},
    children: [
      {
        children: [
          {
            angle: 0.0,
            children: [
              {
                angle: 0.0,
                children: [],
                footprint: {
                  coordinates: [
                    [
                      [-2.1714088983050033, 1.1538771186441181],
                      [2.171408898305117, 1.1538771186441181],
                      [2.171408898305117, -1.1538771186441181],
                      [-2.1714088983050033, -1.1538771186441181],
                      [-2.1714088983050033, 1.1538771186441181],
                    ],
                  ],
                  type: 'Polygon',
                },
                height: [0.0, 17500000.0],
                id: 'f7482d02-fbf4-11e9-8f21-0242ac120005',
                position: { coordinates: [0.0, 0.0], type: 'Point' },
                type: 'AreaType.NOT_DEFINED',
              },
            ],
            footprint: {
              coordinates: [
                [
                  [-2.1714088983050033, 1.1538771186441181],
                  [2.171408898305117, 1.1538771186441181],
                  [2.171408898305117, -1.1538771186441181],
                  [-2.1714088983050033, -1.1538771186441181],
                  [-2.1714088983050033, 1.1538771186441181],
                ],
              ],
              type: 'Polygon',
            },
            has_passage_entrance: null,
            id: 'f7482e9c-fbf4-11e9-8f21-0242ac120005',
            is_public: 0,
            position: { coordinates: [11.64, -11.76], type: 'Point' },
            room_shapes: {},
            sun_simulation: {},
            type: 'SpaceType.NOT_DEFINED',
            view_simulation: {},
          },
        ],
        floor_number: 'f74830f4-fbf4-11e9-8f21-0242ac120005',
        height: null,
        is_complete: 1,
        position: { coordinates: [572.18, -573.7], type: 'Point' },
        type: 'floor',
      },
    ],
    id: 'f748302c-fbf4-11e9-8f21-0242ac120005',
    type: 'LayoutType.NOT_DEFINED',
  };

  /**
   * Example area Types for testing purposes
   */
  public static areaTypes = [
    'BALCONY',
    'BATHROOM',
    'COPYROOM',
    'CORRIDOR',
    'DINING',
    'ELEVATOR',
    'KITCHEN',
    'KITCHEN_DINING',
    'LOGGIA',
    'NOT_DEFINED',
    'REFERENCED',
    'ROOM',
    'SHAFT',
    'STAIRCASE',
    'STOREROOM',
    'WINTERGARTEN',
    'WORKAREA',
  ];
}
