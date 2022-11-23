import React from 'react';
import { useRouter } from 'Common/hooks';
import { getRoomName } from 'Common/modules';
import { C } from 'Common';
import useSWR from 'swr';
import { ProviderRequest } from '../providers';
import { DataView } from '../components';

const { DMS_VIEWS, ENDPOINTS, URLS } = C;
const { CLIENTS, SITES, BUILDINGS, FLOORS, UNITS, ROOMS, CUSTOM_FOLDER, TRASH } = DMS_VIEWS;

const NOT_ENTITY_VIEWS = [CUSTOM_FOLDER, TRASH];

const ENTITY_ENDPOINTS = {
  [CLIENTS]: query => ENDPOINTS.CLIENT(),
  [SITES]: query => ENDPOINTS.SITES_BY_CLIENT(query.client_id),
  [BUILDINGS]: query => ENDPOINTS.BUILDINGS_BY_SITE(query.site_id),
  [FLOORS]: query => ENDPOINTS.FLOORS_BY_BUILDING(query.building_id),
  [UNITS]: query => ENDPOINTS.UNITS_BY_FLOOR(query.floor_id),
  [ROOMS]: query => ENDPOINTS.ROOMS_BY_UNIT(query.unit_id),
  [CUSTOM_FOLDER]: null,
  [TRASH]: null,
};

const ENTITY_NEXT_LEVEL_URL = {
  [CLIENTS]: entity => URLS.SITES_BY_CLIENT(entity.id),
  [SITES]: entity => URLS.BUILDINGS_BY_SITE(entity.id),
  [BUILDINGS]: entity => URLS.FLOORS_BY_BUILDING(entity.id),
  [FLOORS]: entity => URLS.UNITS_BY_FLOOR(entity.id),
  [UNITS]: entity => URLS.ROOMS_BY_UNIT(entity.id),
  [ROOMS]: (entity, query) => URLS.ROOM(entity.id, query.unit_id), // To find file & folders for rooms we need area_id & unit_id
};

const ENTITY_DMS_NAME = {
  [CLIENTS]: client => client.name,
  [SITES]: site => site.name || site.client_site_id || String(site.id),
  [BUILDINGS]: building => `${building.street}, ${building.housenumber}`,
  [FLOORS]: floor => `Floor ${floor.floor_number}`,
  [UNITS]: unit => unit.client_id,
  [ROOMS]: room => getRoomName(room),
};

const useFetchEntities = (pathname, query) => {
  const endpoint = NOT_ENTITY_VIEWS.includes(pathname) ? null : ENTITY_ENDPOINTS[pathname]?.(query);
  const { data = [], isValidating = false } = useSWR(endpoint, ProviderRequest.get);
  return { data, isValidating };
};

// @TODO: Rename onClickItem or onClickEntityOrFolder
const onClickFolder = (pathname, history, entity, query = {}) => {
  const nextLevel = ENTITY_NEXT_LEVEL_URL[pathname](entity, query);
  history.push(nextLevel);
};

const getEntityName = (pathname, entity) => {
  const name = ENTITY_DMS_NAME[pathname]?.(entity);
  return name;
};

const DMS = () => {
  const { query, pathname, history } = useRouter();
  const { data, isValidating } = useFetchEntities(pathname, query);

  return (
    <DataView
      data={data}
      isLoadingEntities={isValidating}
      onClickFolder={entity => onClickFolder(pathname, history, entity, query)}
      getEntityName={entity => getEntityName(pathname, entity)}
    />
  );
};

export default DMS;
