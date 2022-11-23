import useSWR from 'swr';
import { getRoomName } from 'Common/modules';
import { ProviderRequest } from '../../providers';
import { checkAccess } from '../roles';
import { C } from '..';
import { FolderResponse } from '../types';
import useRouter from './router';

const { ENDPOINTS } = C;

// this is how the hierarchy of pages builds in the app
// read this object from bottom to top and from right to left, for example:
// from 'home' to 'clients' then from 'clients' to 'sites' and so on
const hierarchy = {
  room: 'rooms',
  rooms: 'units',
  units: 'floors',
  floors: 'buildings',
  buildings: 'sites',
  sites: 'clients',
  clients: '',
};

const getParentFolder = folder => {
  const parentIsAnotherFolder = folder.parent_folder_id;
  if (parentIsAnotherFolder) {
    return () => PARENT_FROM_ENTITY['custom_folder']({ folder_id: folder.parent_folder_id, isParent: true });
  }
  if (folder.deleted) {
    return () => PARENT_FROM_ENTITY['trash']({ client_id: folder.client_id });
  }
  for (const [entity, parent] of Object.entries(hierarchy)) {
    const parentQuery = `${parent.slice(0, -1)}_id`;
    if (folder[parentQuery]) {
      return () => PARENT_FROM_ENTITY[entity]({ [parentQuery]: folder[parentQuery] });
    }
  }
  return null;
};

const PARENT_FROM_ENTITY = {
  users: async () => {
    return { text: 'All Users', href: '/users' };
  },
  clients: async () => {
    return { text: 'All Clients', href: '/clients' };
  },
  sites: async ({ client_id }) => {
    const client = await ProviderRequest.get(ENDPOINTS.CLIENT(client_id));
    return {
      text: ` ${client.name}`,
      href: `/sites?client_id=${client.id}`,
      parent: checkAccess('/clients') ? () => PARENT_FROM_ENTITY['clients']() : undefined,
    };
  },
  buildings: async ({ site_id }) => {
    const site = await ProviderRequest.get(ENDPOINTS.SITE(site_id));
    return {
      text: ` Site: ${site.name || site.id}`,
      href: `/buildings?site_id=${site.id}`,
      parent: () => PARENT_FROM_ENTITY['sites'](site),
    };
  },
  floors: async ({ building_id }) => {
    const building = await ProviderRequest.get(ENDPOINTS.BUILDING(building_id));
    const buildingName = `${building.street}, ${building.housenumber}`;
    return {
      text: ` Building: ${buildingName}`,
      href: `/floors?building_id=${building.id}`,
      parent: () => PARENT_FROM_ENTITY['buildings'](building),
    };
  },
  units: async ({ floor_id = undefined }) => {
    const floor = await ProviderRequest.get(ENDPOINTS.FLOOR(floor_id));
    return {
      text: `Floor ${floor.floor_number}`,
      href: `/units?floor_id=${floor_id}`,
      parent: () => PARENT_FROM_ENTITY['floors'](floor),
      payload: floor,
    };
  },
  rooms: async ({ unit_id = undefined }) => {
    const unit = await ProviderRequest.get(ENDPOINTS.UNIT(unit_id));
    return {
      text: `Unit ${unit.client_id}`,
      parent: () => PARENT_FROM_ENTITY['units'](unit),
      href: `/rooms?unit_id=${unit.id}`,
      payload: unit,
    };
  },
  room: async ({ unit_id = undefined, area_id }) => {
    const rooms = await ProviderRequest.get(ENDPOINTS.ROOMS_BY_UNIT(unit_id));
    const room = rooms.find(room => String(room.id) === String(area_id));
    return {
      text: getRoomName(room),
      parent: () => PARENT_FROM_ENTITY['rooms']({ unit_id }),
      href: C.URLS.ROOM(area_id, unit_id),
      payload: room,
    };
  },
  pipelines: async ({ site_id, plan_id }) => {
    if (site_id) {
      const site = await ProviderRequest.get(ENDPOINTS.SITE(site_id));
      return { text: ` Pipelines for site: ${site.name}`, parent: () => PARENT_FROM_ENTITY['sites'](site) };
    }
    if (plan_id) {
      const plan = await ProviderRequest.get(ENDPOINTS.PLAN(plan_id));
      return { text: `Pipeline: ${plan_id}`, parent: () => PARENT_FROM_ENTITY['floors'](plan) };
    }
  },
  custom_folder: async ({ folder_id, isParent = false }) => {
    const folder: FolderResponse = await ProviderRequest.get(ENDPOINTS.FOLDER(folder_id));
    const parent = getParentFolder(folder);
    return {
      parent,
      text: `Folder: ${folder.name}`,
      href: isParent ? `/custom_folder?folder_id=${folder.id}` : null,
    };
  },
  trash: ({ client_id }) => {
    return {
      parent: () => PARENT_FROM_ENTITY['sites']({ client_id }),
      text: 'Trash',
      href: `/trash?client_id=${client_id}`,
    };
  },
};

const hasAncestor = entity => entity && entity.parent;

const getHierarchy = async (query, pathname) => {
  const entityName = pathname.split('/').slice(-1)[0];
  let entity = await PARENT_FROM_ENTITY[entityName](query);
  const result: any = [{ ...entity }];

  while (hasAncestor(entity)) {
    const data = await entity.parent();
    result.unshift({ ...data });
    entity = data;
  }

  return result;
};

const useHierarchy = () => {
  const { query, pathname, fullPath } = useRouter();
  const { data: hierarchy = [] } = useSWR(`hierachy-${fullPath}`, () => getHierarchy(query, pathname));
  return hierarchy;
};

export default useHierarchy;
