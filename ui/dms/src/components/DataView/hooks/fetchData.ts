import useSWR from 'swr';
import { ProviderRequest } from 'Providers';
import { useRouter } from 'Common/hooks';
import { NetAreaDistribution, ParentQuery } from 'Common/types';
import { C } from 'Common';
import { getEntityId, getUserClientId, inView } from '../modules';

const useRequest = (endpoint, fetcher) => {
  return useSWR(endpoint, fetcher, { revalidateOnFocus: false });
};

const { DMS_VIEWS } = C;
const { SITES, CLIENTS, FLOORS, BUILDINGS, TRASH, CUSTOM_FOLDER, UNITS, ROOMS } = DMS_VIEWS;

const insideAClient = pathname => inView([SITES, BUILDINGS, FLOORS, UNITS, ROOMS], pathname);

type ResponseNetAreaDistribution = { data?: NetAreaDistribution; isValidating: boolean };
type FetchResponse = { data: any; mutate?: () => void; isValidating: boolean };

const getSiteUnitsEndpoint = (pathname, hierarchy) => {
  if (inView([FLOORS], pathname)) {
    const siteId = getEntityId(hierarchy, 'site_id');
    return siteId ? C.ENDPOINTS.SITE_UNITS(siteId) : null;
  }
  return null;
};

const getSiteEndpoint = hierarchy => {
  const siteId = getEntityId(hierarchy, 'site_id');
  return siteId ? C.ENDPOINTS.SITE(siteId) : null;
};

const getNetAreaDistributionEndpoint = ({ pathname, search }, site, view) => {
  if (!insideAClient(pathname)) {
    return null;
  }
  return C.ENDPOINTS.SITE_NET_AREA_DISTRIBUTION(search);
};

const getUnitEndpoint = ({ pathname, query }) => {
  if (!inView([ROOMS], pathname)) {
    return null;
  }
  return C.ENDPOINTS.UNIT(query.unit_id);
};

// Needed to display the floorplan in rooms view
const getUnitFloorPlanEndpoint = ({ pathname, query }) => {
  if (!inView([ROOMS], pathname)) {
    return null;
  }
  return C.ENDPOINTS.UNIT_FLOOR_PLAN(query.unit_id);
};

const getCustomFoldersEndpoint = ({ search, query, pathname }, hierarchy, view) => {
  if (inView([CUSTOM_FOLDER], pathname) || inView([CLIENTS], pathname)) {
    return null;
  }
  if (inView([TRASH], pathname)) {
    return C.ENDPOINTS.FOLDER_TRASH(getUserClientId(hierarchy, query));
  }
  return C.ENDPOINTS.FOLDER_SEARCH(search);
};

const getCustomSubFoldersEndpoint = ({ query, pathname }) => {
  const { folder_id: folderId } = query;
  if (!inView([CUSTOM_FOLDER], pathname)) return null;
  return C.ENDPOINTS.FOLDER_SUBFOLDERS(folderId);
};

const getFilesEndpoint = ({ search, pathname }, view) => {
  if (inView([CLIENTS], pathname)) return null;
  if (inView([TRASH], pathname)) return C.ENDPOINTS.FILE_TRASH();
  return search ? C.ENDPOINTS.FILE_SEARCH(search) : null;
};

const getCustomFolderFilesEndpoint = ({ pathname, query }, view) => {
  const { folder_id: folderId } = query;
  if (inView([CLIENTS], pathname)) return null;
  if (inView([TRASH], pathname)) return C.ENDPOINTS.FOLDER_FILE_TRASH();
  return C.ENDPOINTS.FOLDER_FILES(folderId);
};

const useFetchFiles = ({ routerData, view }): FetchResponse => {
  const { data, mutate, isValidating } = useRequest(
    inView([CUSTOM_FOLDER], routerData.pathname)
      ? getCustomFolderFilesEndpoint(routerData, view)
      : getFilesEndpoint(routerData, view),
    ProviderRequest.get
  );
  return { data, mutate, isValidating };
};

const useFetchFolders = ({ routerData, hierarchy, view }): FetchResponse => {
  const { data, mutate, isValidating } = useRequest(
    inView([CUSTOM_FOLDER], routerData.pathname)
      ? getCustomSubFoldersEndpoint(routerData)
      : getCustomFoldersEndpoint(routerData, hierarchy, view),
    ProviderRequest.get
  );
  return { data, mutate, isValidating };
};

const useFetchSite = ({ hierarchy }): FetchResponse => {
  const { data = {}, mutate, isValidating } = useRequest(getSiteEndpoint(hierarchy), ProviderRequest.get);
  return { data, mutate, isValidating };
};

const useFetchSiteUnits = ({ routerData, hierarchy }): FetchResponse => {
  const { data = [], isValidating } = useRequest(
    getSiteUnitsEndpoint(routerData.pathname, hierarchy),
    ProviderRequest.get
  );
  return { data, isValidating };
};

const useFetchNetAreaData = ({ routerData, view }, site) => {
  const { data, isValidating }: ResponseNetAreaDistribution = useRequest(
    getNetAreaDistributionEndpoint(routerData, site, view),
    ProviderRequest.get
  );
  return { data, isValidating };
};
const useFetchUnit = ({ routerData }): FetchResponse => {
  const { data, isValidating } = useRequest(getUnitEndpoint(routerData), ProviderRequest.get);
  return { data, isValidating };
};

const useFetchUnitFloorplan = ({ routerData }): FetchResponse => {
  const { data, isValidating } = useRequest(getUnitFloorPlanEndpoint(routerData), ProviderRequest.getBlob);
  return { data, isValidating };
};

const useFetchData = (view, hierarchy, isLoadingEntities) => {
  const { pathname, search = '', query }: { pathname: string; search: string; query: ParentQuery } = useRouter();
  const routerData = { pathname, search, query };
  const fetchParams = { routerData, hierarchy, view };

  const { data: files, mutate: reloadFiles, isValidating: isLoadingFiles } = useFetchFiles(fetchParams);
  const { data: folders, mutate: reloadCustomFolders, isValidating: isLoadingFolders } = useFetchFolders(fetchParams);
  const { data: site, isValidating: isLoadingSite } = useFetchSite(fetchParams);
  const { data: siteUnits, isValidating: isLoadingSiteUnits } = useFetchSiteUnits(fetchParams);
  const { data: netAreaData, isValidating: isLoadingNetAreaData } = useFetchNetAreaData(fetchParams, site);
  const { data: unit, isValidating: isLoadingUnit } = useFetchUnit(fetchParams);
  const { data: unitFloorPlanBlob, isValidating: isLoadingUnitFloorPlan } = useFetchUnitFloorplan(fetchParams);

  const loadingState = {
    site: isLoadingSite,
    unit: isLoadingUnit,
    unitFloorPlan: isLoadingUnitFloorPlan,
    units: isLoadingSiteUnits,
    files: isLoadingFiles,
    folders: isLoadingFolders,
    areaData: isLoadingNetAreaData,
    entities: isLoadingEntities,
  };

  return {
    unitFloorPlanBlob,
    netAreaData,
    files,
    folders,
    site,
    siteUnits,
    unit,
    reloadFiles,
    reloadCustomFolders,
    loadingState,
  };
};

export default useFetchData;
