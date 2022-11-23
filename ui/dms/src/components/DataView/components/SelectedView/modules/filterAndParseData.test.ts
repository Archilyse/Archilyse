import { C } from 'Common';
import filterAndParseData from './filterAndParseData';

const { UNITS, FLOORS, SITES } = C.DMS_VIEWS;
const MOCK_ENTITIES = [
  {
    created: '2020-09-11T12:05:51.365226',
    id: 1488,
    labels: null,
    lat: 47.354772751639786,
    lon: 8.55859203736299,
    name: 'Münchhaldenstrasse',
  },
  {
    created: '2021-02-02T16:36:51.418522',
    id: 2436,
    labels: null,
    lat: 47.508353460069685,
    lon: 8.707292981874708,
    name: 'Wülflingerstrasse V1',
  },
  {
    created: '2021-02-02T16:44:35.550843',
    id: 2437,
    labels: null,
    lat: 47.508353460069685,
    lon: 8.707292981874708,
    name: 'Wülflingerstrasse V2',
  },
  {
    created: '2021-02-02T16:44:35.550843',
    id: 2437,
    labels: null,
    lat: 47.508353460069685,
    lon: 8.707292981874708,
    name: '',
  },
];

const MOCK_FILES = [
  {
    building_id: null,
    checksum: '+cn4yBONBpp+Y2wutDQtOQ==',
    client_id: 71,
    comments: [],
    content_type: 'image/jpeg',
    created: '2021-01-29T13:57:00.160873',
    creator_id: 220,
    deleted: false,
    floor_id: null,
    folder_id: null,
    id: 50,
    labels: [],
    name: '-1.jpeg',
    site_id: null,
    size: 438668,
    unit_id: null,
    updated: null,
  },
  {
    building_id: null,
    checksum: '+cn4yBONBpp+Y2wutDQtOQ==',
    client_id: 71,
    comments: [],
    content_type: 'image/jpeg',
    created: '2021-01-29T13:57:00.160873',
    creator_id: 220,
    deleted: false,
    floor_id: null,
    folder_id: null,
    id: 50,
    labels: [],
    name: 'toalaimagen.jpeg',
    site_id: null,
    size: 1232,
    unit_id: null,
    updated: null,
  },
];

const MOCK_FOLDERS = [
  {
    building_id: null,
    client_id: 71,
    created: '2021-03-19T08:03:54.533129',
    creator_id: 86,
    deleted: false,
    floor_id: null,
    id: 5659,
    labels: [],
    name: 'test',
    parent_folder_id: null,
    site_id: null,
    unit_id: null,
    updated: null,
  },
];

const MOCK_FLOOR_FOLDERS = [
  {
    created: '2021-03-19T08:03:54.533129',
    id: 12248,
    labels: [],
    name: 'Floor 1',
    type: 'folder-floors',
  },
  {
    created: '2021-03-19T08:03:54.533129',
    id: 12245,
    labels: [],
    name: 'Floor 2',
    type: 'folder-floors',
  },
];

const CURRENT_UNITS = [
  {
    apartment_no: 1,
    client_id: 'ABC0201',
    created: '2020-05-17T13:34:44.350964',
    floor_id: 12245,
    id: 61584,
    labels: null,
    ph_final_gross_rent_adj_factor: 0.03,
    ph_final_gross_rent_annual_m2: 100,
    ph_final_sale_price_adj_factor: 0.02,
    ph_final_sale_price_m2: 500,
    plan_id: 7462,
    site_id: 1439,
    unit_type: 'B',
    unit_usage: 'RESIDENTIAL',
    updated: '2022-03-29T07:46:28.918984',
  },
  {
    apartment_no: 1,
    client_id: 'ABC0401',
    created: '2020-05-17T13:34:44.350964',
    floor_id: 12248,
    id: 61584,
    labels: null,
    ph_final_gross_rent_adj_factor: 0.03,
    ph_final_gross_rent_annual_m2: 100,
    ph_final_sale_price_adj_factor: 0.02,
    ph_final_sale_price_m2: 500,
    plan_id: 7462,
    site_id: 1439,
    unit_type: 'B',
    unit_usage: 'RESIDENTIAL',
    updated: '2022-03-29T07:46:28.918984',
  },
  {
    apartment_no: 1,
    client_id: 'ABC0301',
    created: '2020-05-17T13:59:10.863812',
    floor_id: 12245,
    id: 61588,
    labels: null,
    ph_final_gross_rent_adj_factor: -0.09,
    ph_final_gross_rent_annual_m2: 200,
    ph_final_sale_price_adj_factor: 0.02,
    ph_final_sale_price_m2: 500,
    ph_net_area: null,
    plan_id: 7463,
    site_id: 1439,
    unit_type: 'B',
    unit_usage: 'RESIDENTIAL',
    updated: '2022-03-29T07:46:28.919006',
  },
  {
    apartment_no: 1,
    client_id: 'ABC0302',
    created: '2020-05-17T13:59:10.863812',
    floor_id: 12248,
    id: 61588,
    labels: null,
    ph_final_gross_rent_adj_factor: -0.09,
    ph_final_gross_rent_annual_m2: 200,
    ph_final_sale_price_adj_factor: 0.02,
    ph_final_sale_price_m2: 500,
    ph_net_area: null,
    plan_id: 7463,
    site_id: 1439,
    unit_type: 'B',
    unit_usage: 'RESIDENTIAL',
    updated: '2022-03-29T07:46:28.919006',
  },
];

const EXPECTED_PARSED_FIELDS = ['created', 'id', 'labels', 'name', 'type'];
const assertExpectedParse = filteredData => {
  for (const item of filteredData) {
    for (const field of EXPECTED_PARSED_FIELDS) {
      expect(item[field]).toBeTruthy();
    }
  }
};

const assertExpectedFloorParse = filteredData => {
  for (const floor of filteredData) {
    expect(floor.phFactor).toEqual(-0.03);
    expect(floor.phPrice).toEqual(500);
  }
};

describe('filterAndParseData function', () => {
  const MOCK_ARGUMENTS = {
    getEntityName: () => {},
    filter: '',
    entitiesData: MOCK_ENTITIES,
    files: MOCK_FILES,
    customFolders: MOCK_FOLDERS,
    pathname: SITES,
    currentUnits: [],
    areaData: {},
  };
  const totalDataLength = MOCK_ENTITIES.length + MOCK_FOLDERS.length + MOCK_FILES.length;
  it('Filters empty data', () => {
    const filteredData = filterAndParseData({ ...MOCK_ARGUMENTS, entitiesData: [], customFolders: [], files: [] });
    expect(filteredData).toEqual([]);
  });

  it('Parse entities data without filter inside sites', () => {
    const filteredData = filterAndParseData({ ...MOCK_ARGUMENTS });
    expect(filteredData.length).toEqual(totalDataLength);
    assertExpectedParse(filteredData);
  });

  it('Filters a single site', () => {
    const filter = MOCK_ENTITIES[0].name;
    const filteredData = filterAndParseData({
      ...MOCK_ARGUMENTS,
      filter,
    });
    expect(filteredData.length).toEqual(1);
    assertExpectedParse(filteredData);
  });

  it('Uses the name field in the entities when there is no getEntityName', () => {
    const filteredData = filterAndParseData({
      ...MOCK_ARGUMENTS,
      entitiesData: MOCK_ENTITIES,
      files: MOCK_FILES,
      customFolders: MOCK_FOLDERS,
      getEntityName: undefined,
      pathname: SITES,
    });
    expect(filteredData.length).toEqual(totalDataLength);
    assertExpectedParse(filteredData);
    const parsedSites = filteredData.filter(item => item.type === 'folder-sites');

    const EXPECTED_NAMES = MOCK_ENTITIES.slice(0, 3).map(site => site.name);
    const siteWithoutName = MOCK_ENTITIES.slice(-1)[0];
    EXPECTED_NAMES.push(String(siteWithoutName.id));

    for (const site of parsedSites) {
      expect(EXPECTED_NAMES.includes(site.name)).toBeTruthy();
    }
  });

  it('Uses `getEntityName` to name every entity', () => {
    const getEntityName = site => site.id;
    const filteredData = filterAndParseData({
      ...MOCK_ARGUMENTS,
      entitiesData: MOCK_ENTITIES,
      files: MOCK_FILES,
      customFolders: MOCK_FOLDERS,
      getEntityName,
      pathname: SITES,
    });
    expect(filteredData.length).toEqual(totalDataLength);
    assertExpectedParse(filteredData);
    const parsedSites = filteredData.filter(item => item.type === 'folder-sites');

    for (const site of parsedSites) {
      expect(site.name).toEqual(getEntityName(site));
    }
  });

  it('Computes unit PH prices as the m2 * chf/m2', () => {
    const MOCK_AREA_DATA = {
      floors: [], // Irrelevant for this test
      units: CURRENT_UNITS.map((unit, index) => ({ id: unit.id, netArea: index + 1 })),
    };
    const filteredData = filterAndParseData({
      ...MOCK_ARGUMENTS,
      entitiesData: CURRENT_UNITS,
      pathname: UNITS,
      currentUnits: CURRENT_UNITS,
      areaData: MOCK_AREA_DATA,
    });
    const parsedUnits = filteredData.filter(item => item.type === 'folder-units');

    parsedUnits.forEach(unit => {
      const netArea = MOCK_AREA_DATA.units.find(u => String(u.id) === String(unit.id))?.netArea || 1;
      const pricePerM2 = CURRENT_UNITS.find(u => String(u.id) === String(unit.id)).ph_final_gross_rent_annual_m2;
      expect(unit.phPrice).toBe(pricePerM2 * netArea);
    });
  });

  it('Computes floor PH values as the sum of the total ph prices of the corresponding units', () => {
    const MOCK_AREA_DATA = {
      floors: [], // Irrelevant for this test
      units: CURRENT_UNITS.map((unit, index) => ({ id: unit.id, netArea: index })),
    };
    const filteredData = filterAndParseData({
      ...MOCK_ARGUMENTS,
      entitiesData: MOCK_FLOOR_FOLDERS,
      pathname: FLOORS,
      currentUnits: CURRENT_UNITS,
      areaData: MOCK_AREA_DATA,
    });
    const parsedFloors = filteredData.filter(item => item.type === 'folder-floors');
    assertExpectedFloorParse(parsedFloors);
  });
});
