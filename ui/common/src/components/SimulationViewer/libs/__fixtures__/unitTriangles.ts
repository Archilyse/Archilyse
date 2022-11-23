import { ThreeDUnit } from '../../../../types';

export const mockedUnitsTriangles1: ThreeDUnit[] = [
  [
    'any',
    [
      [
        [1, 2, 250],
        [3, 4, 251],
        [5, 6, 249],
      ],
    ],
  ],
];

export const mockedUnitsTriangles2: ThreeDUnit[] = [
  ...mockedUnitsTriangles1,
  [
    'any',
    [
      [
        [7, 8, 255],
        [5, 3, 256],
        [8, 9, 254],
      ],
    ],
  ],
];

export const mockedUnitsTriangles3: ThreeDUnit[] = [
  ...mockedUnitsTriangles2,
  [
    'any',
    [
      [
        [1, 2, 241],
        [2, 1, 240],
        [1, -1, 239],
      ],
    ],
  ],
];
