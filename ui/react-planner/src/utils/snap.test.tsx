import { MOCK_SCENE } from '../tests/utils';
import { SNAPS } from '../constants';
import { GeometryUtils, SnapUtils } from '../utils/export';

const radToDeg = angle => (angle * 180) / Math.PI;

describe('SnapUtils', () => {
  const assertPerpToGridSnaps = (snaps, { x, y }) => {
    const expectedSnaps = snaps;

    // Four snaps created
    expect(expectedSnaps.length).toBe(4);

    // Every one of them starts on the initial point
    for (const snap of expectedSnaps) {
      expect(GeometryUtils.samePoints({ x: snap.x1, y: snap.y1 }, { x, y })).toBeTruthy();
    }

    const [perpendicularSnaps1, perpendicularSnaps2, parallelSnaps1, parallelSnaps2] = expectedSnaps;

    // Two perpendicular lines
    let angle = GeometryUtils.angleBetweenTwoPoints(x, y, perpendicularSnaps1.x2, perpendicularSnaps1.y2);
    expect(radToDeg(angle)).toBe(90);

    angle = GeometryUtils.angleBetweenTwoPoints(x, y, perpendicularSnaps2.x2, perpendicularSnaps2.y2);
    expect(radToDeg(angle)).toBe(-90);

    // Two parallel lins
    angle = GeometryUtils.angleBetweenTwoPoints(x, y, parallelSnaps1.x2, parallelSnaps1.y2);
    expect(radToDeg(angle)).toBe(0);

    angle = GeometryUtils.angleBetweenTwoPoints(x, y, parallelSnaps2.x2, parallelSnaps2.y2);
    expect(radToDeg(angle)).toBe(180);
  };

  const assertPerpToLineSnaps = (snaps, { x, y }) => {
    const expectedSnaps = snaps;

    // Four snaps created
    expect(expectedSnaps.length).toBe(4);

    // Every one of them starts on the initial point
    const [perpendicularSnaps1, perpendicularSnaps2, parallelSnaps1] = expectedSnaps;

    for (const snap of [perpendicularSnaps1, perpendicularSnaps2]) {
      expect(Math.round(snap.x1)).toEqual(x);
      expect(Math.round(snap.x2)).toEqual(x);
    }
    for (const snap of [parallelSnaps1, parallelSnaps1]) {
      expect(Math.round(snap.y1)).toEqual(y);
      expect(Math.round(snap.y2)).toEqual(y);
    }
  };

  describe('addPerpendicularSnapLines', () => {
    let scene;
    let snapElements;
    let MOCK_LAYER;
    // let scene = MOCK_SCENE;
    // let snapElements = [];
    // let MOCK_LAYER = {
    //   vertices: {
    //     a: { x: 352, y: 1405 },
    //     b: { x: 701, y: 1405 },

    //     aux1: { x: 352, y: 1425 },
    //     aux2: { x: 701, y: 1425 },
    //     aux3: { x: 352, y: 1445 },
    //     aux4: { x: 701, y: 1445 },
    //   },
    //   lines: { line1: { id: 'line1', vertices: ['a', 'b'], auxVertices: ['aux1', 'aux2', 'aux3', 'aux4'] } },
    // };
    beforeEach(() => {
      scene = MOCK_SCENE;
      snapElements = [];
      MOCK_LAYER = {
        vertices: {
          a: { x: 352, y: 1405 },
          b: { x: 701, y: 1405 },

          aux1: { x: 352, y: 1425 },
          aux2: { x: 701, y: 1425 },
          aux3: { x: 352, y: 1445 },
          aux4: { x: 701, y: 1445 },
        },
        lines: { line1: { id: 'line1', vertices: ['a', 'b'], auxVertices: ['aux1', 'aux2', 'aux3', 'aux4'] } },
      };
    });

    it('Without intersecting with any line, creates two parallel and perpendicular snap segments', () => {
      const startingPoint = { x: 500, y: 1000 };
      const layer = { lines: {} };
      const snaps = SnapUtils.addPerpendicularSnapLines(scene, snapElements, startingPoint, layer);
      assertPerpToGridSnaps(snaps, startingPoint);
    });

    it('Intersecting with a line on its main reference line, creates two parallel and perpendicular snap segments', () => {
      const startingPoint = { x: MOCK_LAYER.vertices.a.x, y: MOCK_LAYER.vertices.a.y };
      const snaps = SnapUtils.addPerpendicularSnapLines(scene, snapElements, startingPoint, MOCK_LAYER);
      // const perpToGridSnaps = snaps.skip(4);
      const _perpToGridSnaps = snaps.slice(4);
      const perpToLineSnaps = snaps.slice(0, 4);
      // assertPerpToGridSnaps(perpToGridSnaps, startingPoint);
      assertPerpToLineSnaps(perpToLineSnaps, startingPoint);
    });

    it('Intersecting with a line on one of its aux reference lines, creates two parallel and perpendicular snap segments', () => {
      const scene = MOCK_SCENE;
      const startingPoint = { x: 600, y: 1445 }; // Intersects with ref line created by aux3 & aux 4
      const snaps = SnapUtils.addPerpendicularSnapLines(scene, snapElements, startingPoint, MOCK_LAYER);
      // const perpToGridSnaps = snaps.skip(4);
      const _perpToGridSnaps = snaps.slice(4);
      const perpToLineSnaps = snaps.slice(0, 4);

      // assertPerpToGridSnaps(perpToGridSnaps, startingPoint);
      assertPerpToLineSnaps(perpToLineSnaps, startingPoint);
    });
  });

  describe('getSnapsFromItemCentroid', () => {
    it('Given an item in 0,0 with 0 angle, the snapping points are all around in the axis', () => {
      const snapElements = [];
      const [x, y, itemAngle, widthInPixels, lengthInPixels, newItemwidthInPixels, newLengthInPixels] = [
        0,
        0,
        0,
        10,
        10,
        50,
        50,
      ];
      const snaps = SnapUtils.getSnapsFromItemCentroid(
        snapElements,
        { x, y },
        itemAngle,
        widthInPixels,
        lengthInPixels,
        newItemwidthInPixels,
        newLengthInPixels
      );
      expect(snaps.length).toBe(4);
      // The value 30 comes from half of the widthInPixels/lengthInPixels + the half of the new item (newItemwidthInPixels/newLengthInPixels)
      const expectedX = [0, -0, 30, -30];
      const expectedY = [30, -30, 0, 0];
      const allx = snaps.map(snap => Math.round(snap.x));
      const ally = snaps.map(snap => Math.round(snap.y));
      snaps.forEach(snap => {
        expect(snap.metadata['SnappingAngle']).toBe(0);
      });

      expect(allx).toStrictEqual(expectedX);
      expect(ally).toStrictEqual(expectedY);
    });

    it('Given an item in 0,0 with 180 degrees angle, the snapping points are all around in the axis with only the order of the snapping different to the previous test', () => {
      const snapElements = [];
      const [x, y, itemAngle, widthInPixels, lengthInPixels, newItemwidthInPixels, newLengthInPixels] = [
        0,
        0,
        180,
        10,
        10,
        50,
        50,
      ];
      const snaps = SnapUtils.getSnapsFromItemCentroid(
        snapElements,
        { x, y },
        itemAngle,
        widthInPixels,
        lengthInPixels,
        newItemwidthInPixels,
        newLengthInPixels
      );
      expect(snaps.length).toBe(4);
      // The value 30 comes from half of the widthInPixels/lengthInPixels + the half of the new item (newItemwidthInPixels/newLengthInPixels)
      const expectedX = [-0, 0, -30, 30];
      const expectedY = [-30, 30, 0, -0];
      const allx = snaps.map(snap => Math.round(snap.x));
      const ally = snaps.map(snap => Math.round(snap.y));
      // check the angle of the item to be snapped to
      snaps.forEach(snap => {
        expect(snap.metadata['SnappingAngle']).toBe(180);
      });
      expect(allx).toStrictEqual(expectedX);
      expect(ally).toStrictEqual(expectedY);
    });
  });

  describe('getItemSnapsAroundAreas', () => {
    let snapElements;
    const areasCoords = [
      [
        [
          [0, 0],
          [0, 500],
          [500, 500],
          [500, 0],
          [0, 0],
        ],
      ],
    ];

    beforeEach(() => {
      snapElements = [];
    });

    it('Given a proportional item in the center of a square we get the snapping lines as they come (already buffered based on item length)', () => {
      const itemDimensions = { width: 60, length: 60 };
      const snaps = SnapUtils.getItemSnapsAroundAreas(snapElements, areasCoords, itemDimensions, 180);
      const lineSnaps = snaps.filter(element => element.type === 'line-segment');
      expect(lineSnaps.length).toBe(4);

      // each angle is aiming from the wall to the area
      const expectedAngles = [90, 0, 270, 180];
      // The snapping lines are defined by x1, y1 to x2, y2 pairs
      const expectedX1 = [0, 0, 500, 500];
      const expectedX2 = [0, 500, 500, 0];
      const expectedY1 = [0, 500, 500, 0];
      const expectedY2 = [500, 500, 0, 0];
      const allx1 = lineSnaps.map(snap => Math.round(snap.x1));
      const ally1 = lineSnaps.map(snap => Math.round(snap.y1));
      const allx2 = lineSnaps.map(snap => Math.round(snap.x2));
      const ally2 = lineSnaps.map(snap => Math.round(snap.y2));
      const allAngles = lineSnaps.map(snap => snap.metadata['SnappingAngle']);
      for (let i = 0; i < allAngles.length; i++) {
        expect(allAngles[i]).toBeCloseTo(expectedAngles[i], 6);
      }
      expect(allx1).toStrictEqual(expectedX1);
      expect(ally1).toStrictEqual(expectedY1);
      expect(allx2).toStrictEqual(expectedX2);
      expect(ally2).toStrictEqual(expectedY2);

      // Check also the snapping in the corners of the area
      const pointSnaps = snaps.filter(element => element.type === 'point');
      expect(pointSnaps.length).toBe(4);

      // Check the snapping points in the corners don't have an angle
      pointSnaps.forEach(pointSnap => {
        // console.log(`pointSnap`, pointSnap)
        expect(JSON.stringify(pointSnap.metadata)).toBe('{}');
      });

      const pointsX = pointSnaps.map(snap => Math.round(snap.x));
      const pointsY = pointSnaps.map(snap => Math.round(snap.y));
      const expectedX = [0, 500, 500, 0];
      const expectedY = [500, 500, 0, 0];
      expect(pointsX).toStrictEqual(expectedX);
      expect(pointsY).toStrictEqual(expectedY);
    });

    const TEST_CASE_1 = [
      { width: 100, length: 60 },
      [
        [
          [0, 20],
          [-0, 480],
        ],
        [
          [20, 500],
          [480, 500],
        ],
        [
          [500, 480],
          [500, 20],
        ],
        [
          [480, -0],
          [20, 0],
        ],
      ],
      [
        [0, 20],
        [-0, 480],
        [20, 500],
        [480, 500],
        [500, 480],
        [500, 20],
        [480, -0],
        [20, 0],
      ],
    ];

    const TEST_CASE_2 = [
      { width: 40, length: 60 },
      [
        [
          [-0, -10],
          [0, 510],
        ],
        [
          [-10, 500],
          [510, 500],
        ],
        [
          [500, 510],
          [500, -10],
        ],
        [
          [510, 0],
          [-10, -0],
        ],
      ],
      [
        [-0, -10],
        [0, 510],
        [-10, 500],
        [510, 500],
        [500, 510],
        [500, -10],
        [510, 0],
        [-10, -0],
      ],
    ];

    const TEST_CASE_3 = [
      { width: 42, length: 63 },
      [
        [
          [-0, -11],
          [0, 511],
        ],
        [
          [-11, 500],
          [511, 500],
        ],
        [
          [500, 511],
          [500, -11],
        ],
        [
          [511, 0],
          [-11, -0],
        ],
      ],
      [
        [-0, -11],
        [0, 511],
        [-11, 500],
        [511, 500],
        [500, 511],
        [500, -11],
        [511, 0],
        [-11, -0],
      ],
    ];

    it.each([
      ['non proportional item with width > length', ...TEST_CASE_1],
      ['non proportional item with width < length', ...TEST_CASE_2],
      ['non proportional item with odd width & length', ...TEST_CASE_3],
    ])(
      'Given a %s in the center of a square we get the snapping lines calculated by the item width and length',
      (_, itemDimensions, EXPECTED_LINE_SNAPS, EXPECTED_POINT_SNAPS) => {
        const snaps = SnapUtils.getItemSnapsAroundAreas(snapElements, areasCoords, itemDimensions, 180);
        const lineSnaps = snaps.filter(element => element.type === 'line-segment');
        const lineSnapTuples = lineSnaps.map(snap => [
          [snap.x1, snap.y1],
          [snap.x2, snap.y2],
        ]);
        expect(lineSnaps.length).toBe(4);

        // When the item is not proportional, snapping lines are no longer intersecting so we're adding point to both vertices of the line
        const pointSnaps = snaps.filter(element => element.type === 'point');
        const pointSnapTuples = pointSnaps.map(snap => [snap.x, snap.y]);
        expect(pointSnaps.length).toBe(8);

        lineSnapTuples.forEach((lineTuples, i) => {
          lineTuples.forEach((lineTuple, j) => {
            expect(lineTuple).toStrictEqual(EXPECTED_LINE_SNAPS[i][j]);
          });
        });

        pointSnapTuples.forEach((pointTuple, i) => expect(pointTuple).toStrictEqual(EXPECTED_POINT_SNAPS[i]));
      }
    );
  });

  describe('nearestSnap', () => {
    const snapElements = [
      new SnapUtils.PointSnap({
        x: 300,
        y: 1901,
        radius: SNAPS.POINT.RADIUS,
        priority: SNAPS.POINT.PRIORITY,
      }),
      new SnapUtils.PointSnap({
        x: 701,
        y: 1901,
        radius: SNAPS.POINT.RADIUS,
        priority: SNAPS.POINT.PRIORITY,
      }),
      new SnapUtils.PointSnap({
        x: 300,
        y: 1886.928397390489,
        radius: SNAPS.POINT.RADIUS,
        priority: SNAPS.POINT.PRIORITY,
      }),
      new SnapUtils.LineSegmentSnap({
        x1: 300,
        y1: 1901,
        x2: 701,
        y2: 1901,
        radius: SNAPS.SEGMENT.RADIUS,
        priority: SNAPS.SEGMENT.PRIORITY,
      }),
      new SnapUtils.LineSegmentSnap({
        x1: 300,
        y1: 1886.928397390489,
        x2: 701,
        y2: 1886.928397390489,
        radius: SNAPS.SEGMENT.RADIUS,
        priority: SNAPS.SEGMENT.PRIORITY,
      }),
      new SnapUtils.LineSegmentSnap({
        x1: 300,
        y1: 1872.856794780978,
        x2: 701,
        y2: 1872.856794780978,
        radius: SNAPS.SEGMENT.RADIUS,
        priority: SNAPS.SEGMENT.PRIORITY,
      }),
    ];

    it('Should return nearest rounded points', () => {
      const points = {
        x: 501,
        y: 1901,
      };
      const {
        point: { x, y },
      } = SnapUtils.nearestSnap(snapElements, points.x, points.y, SnapUtils.SNAP_MASK);
      const [roundedX, roundedY] = [GeometryUtils.roundCoord(x), GeometryUtils.roundCoord(y)];
      expect(x).toStrictEqual(roundedX);
      expect(y).toStrictEqual(roundedY);
    });
  });
});
