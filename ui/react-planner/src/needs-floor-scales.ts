import { RequestStatusType } from './constants';

export default ({
  isScaling,
  requestStatus = {},
  floorScales,
  siteStructure,
}: {
  isScaling: boolean;
  requestStatus: { status?: typeof RequestStatusType[keyof typeof RequestStatusType] };
  floorScales: any;
  siteStructure: any;
}) => {
  const isSiteStructureLoaded = siteStructure && siteStructure.planId;

  const hasFloorScales =
    (floorScales && floorScales.length > 0) || requestStatus.status === RequestStatusType.FULFILLED;
  const isLoadingFloorScales = requestStatus.status === RequestStatusType.PENDING;

  return Boolean(isScaling && isSiteStructureLoaded && !hasFloorScales && !isLoadingFloorScales);
};
