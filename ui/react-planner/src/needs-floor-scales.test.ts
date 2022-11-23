import { RequestStatusType } from './constants';
import needsFloorScales from './needs-floor-scales';

const MOCK_ARGS = { isScaling: true, floorScales: [], requestStatus: {}, siteStructure: { planId: 4 } };

describe('needsFloorScales', () => {
  it.each([
    ['When is not scaling', false, { ...MOCK_ARGS, isScaling: false }],
    ['When there is no site structure', false, { ...MOCK_ARGS, siteStructure: null }],
    ['When there are floor scales', false, { ...MOCK_ARGS, floorScales: [{ floorNumber: 1, planId: 1, scale: 1 }] }],
    ['When request is pending', false, { ...MOCK_ARGS, requestStatus: { status: RequestStatusType.PENDING } }],
    [
      'When request is fulfilled, even with no floor scales',
      false,
      { ...MOCK_ARGS, floorScales: undefined, requestStatus: { status: RequestStatusType.FULFILLED } },
    ],
    ['When is scaling, with site structure and no floor scales nor request pending', true, MOCK_ARGS],
  ])('%s returns %s', (description, result, args) => {
    expect(needsFloorScales(args)).toBe(result);
  });
});
