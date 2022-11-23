import {
  inView,
  parseDMSFloorItem,
  parseDMSItem,
  parseDMSSiteItem,
  parseDMSUnitItem,
} from 'Components/DataView/modules';
import { DMSItem, File, Folder } from 'Common/types';
import { C } from 'Common';

const { DMS_VIEWS } = C;
const { FLOORS, ROOMS, ROOM } = DMS_VIEWS;
const DMS_SEARCHABLE_COLUMNS = ['name', 'labels'];

const CUSTOM_FOLDER_TYPE = 'custom-folder';

const setFloorPHValues = (floor, units, unitAreaData = []) => {
  let sumProduct = 0;
  units.forEach(unit => {
    if (floor.id === unit.floor_id) {
      const netArea = unitAreaData.find(u => String(u.id) === String(unit.id))?.netArea || 1;
      sumProduct += unit.ph_final_gross_rent_annual_m2 * unit.ph_final_gross_rent_adj_factor;
      floor.phPrice += unit.ph_final_gross_rent_annual_m2 * netArea;
    }
  });

  floor.phFactor = sumProduct / floor.phPrice;
};

const parseEntities = (data, getEntityName) => {
  return data.map((item: DMSItem) => {
    const name: string = getEntityName?.(item) || item.name || String(item.id) || '';
    return { ...item, name };
  });
};

type ItemFromAPI = (File | Folder) & { unit_id?: number; area_id?: number };

const belongsToAUnit = (item: ItemFromAPI) => item.unit_id && !item.area_id;
const belongsToaRoom = (item: ItemFromAPI) => item.area_id && item.unit_id;

const getDMSData = (folders, customFolders = [], files = [], pathname = '', unitAreaData = []) => {
  const context = pathname.split('/')[1];
  let parsedFolders;
  if (context === 'sites') {
    parsedFolders = folders.map(folder => parseDMSSiteItem(folder, `folder-${context}`));
  } else if (context === 'units') {
    parsedFolders = folders.map(folder => {
      const netArea = unitAreaData.find(unit => String(unit.id) === String(folder.id))?.netArea;
      return parseDMSUnitItem(folder, `folder-${context}`, netArea);
    });
  } else if (context === 'floors') {
    parsedFolders = folders.map(folder => parseDMSFloorItem(folder, `folder-${context}`));
  } else {
    parsedFolders = folders.map(folder => parseDMSItem(folder, `folder-${context}`));
  }

  // @TODO: Hack to deal with items that may belong to area/unit so they don't show in both places
  // as API returns both for now
  let filterFn = item => item;
  if (inView([ROOMS], pathname)) filterFn = belongsToAUnit;
  else if (inView([ROOM], pathname)) filterFn = belongsToaRoom;

  const parsedCustomFolders = customFolders
    .filter(filterFn)
    .map(customFolder => parseDMSItem(customFolder, CUSTOM_FOLDER_TYPE));

  const parsedFiles = files.filter(filterFn).map(file => parseDMSItem(file, file.content_type || file.type));
  return [...parsedFolders, ...parsedCustomFolders, ...parsedFiles];
};

// @TODO We can have some issues on the table if we try to filter in floor by name, for example
// to avoid that we should pass the columns of the DMS <Table/> here, not the admin ones
const filterAndParseData = ({
  entitiesData = [],
  areaData,
  filter,
  getEntityName,
  customFolders,
  files,
  pathname,
  currentUnits,
}) => {
  const entities = parseEntities(entitiesData, getEntityName);
  const dmsData = getDMSData(entities, customFolders, files, pathname, areaData?.units);
  if (inView([FLOORS], pathname)) {
    dmsData.forEach(floor => setFloorPHValues(floor, currentUnits, areaData?.units));
  }
  if (!filter) {
    return dmsData;
  }
  const headers = DMS_SEARCHABLE_COLUMNS;
  return dmsData.filter(row => {
    return Object.entries(row).some(([key, cell = '']) => {
      const visible = headers.includes(key);
      return visible && String(cell).toLowerCase().includes(filter.toLowerCase());
    });
  });
};

export default filterAndParseData;
