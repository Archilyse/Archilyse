import useSWR from 'swr';
import { ProviderRequest } from '../../providers';
import { checkAccess } from '../roles';
import { C } from '..';
import useRouter from './router';

const { ENDPOINTS } = C;

// this is how the hierarchy of pages builds in the app
// read this object from bottom to top and from right to left, for example:
// from 'home' to 'clients' then from 'clients' to 'sites' and so on
/* const hierarchy = {
  rooms: 'units',
  units: 'floors',
  floors: 'buildings',
  buildings: 'sites',
  sites: 'clients',
  clients: '',
}; */

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
    const site = await ProviderRequest.get(ENDPOINTS.SITE_BY_ID(site_id));
    return {
      text: ` Site: ${site.name || site.id}`,
      href: `/buildings?site_id=${site.id}`,
      parent: () => PARENT_FROM_ENTITY['sites'](site),
    };
  },
  floors: async ({ building_id }) => {
    const building = await ProviderRequest.get(ENDPOINTS.BUILDING(building_id));
    return {
      text: ` Building: ${building.id}`,
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
  pipelines: async ({ site_id, plan_id }) => {
    if (site_id) {
      const site = await ProviderRequest.get(ENDPOINTS.SITE_BY_ID(site_id));
      return { text: ` Pipelines for site: ${site.name}`, parent: () => PARENT_FROM_ENTITY['sites'](site) };
    }
    if (plan_id) {
      const plan = await ProviderRequest.get(ENDPOINTS.PLAN(plan_id));
      return { text: `Pipeline: ${plan_id}`, parent: () => PARENT_FROM_ENTITY['floors'](plan) };
    }
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
