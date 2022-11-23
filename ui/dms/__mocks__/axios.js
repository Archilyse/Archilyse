const MOCK_BUILDING = require('./entities/building');
const MOCK_CLIENT = require('./entities/client');
const MOCK_FLOOR = require('./entities/floor');
const MOCK_SITE = require('./entities/site');
const MOCK_UNITS = require('./entities/units');
const MOCK_FLOORS_BY_BUILDING = require('./entities/floors_by_building');
const MOCK_PIPELINES_BY_SITE = require('./entities/pipelines_by_site');
const MOCK_FOLDER = require('./entities/folder');

const URL_REGEXPS = {
  UNITS: /^\/plan\/[0-9]+\/units\?floor_id=[0-9]*$/,
  FLOOR: /^\/floor\/[0-9]+$/,
  BUILDING: /^\/building\/[0-9]+$/,
  SITE: /^\/site\/[0-9]+$/,
  CLIENT: /^\/client\/[0-9]+$/,
  FLOORS_BY_BUILDING: /^\/floor\/\?building_id=[0-9]+$/,
  PIPELINES_BY_SITE: /^\/site\/[0-9]+\/pipeline$/,
  FOLDER: /^\/folder\/[0-9]+$/,
  FOLDER_FILES: /^\/folder\/[0-9]+\/files$/,
};

const {
  UNITS,
  FLOOR,
  BUILDING,
  SITE,
  CLIENT,
  FLOORS_BY_BUILDING,
  PIPELINES_BY_SITE,
  FOLDER,
  FOLDER_FILES,
} = URL_REGEXPS;

module.exports = {
  get: jest.fn(url => {
    if (CLIENT.test(url)) {
      return Promise.resolve({
        data: MOCK_CLIENT,
      });
    }
    if (SITE.test(url)) {
      return Promise.resolve({
        data: MOCK_SITE,
      });
    }
    if (BUILDING.test(url)) {
      return Promise.resolve({
        data: MOCK_BUILDING,
      });
    }
    if (FLOOR.test(url)) {
      return Promise.resolve({
        data: MOCK_FLOOR,
      });
    }
    if (UNITS.test(url)) {
      return Promise.resolve({
        data: MOCK_UNITS,
      });
    }
    if (FLOORS_BY_BUILDING.test(url)) {
      return Promise.resolve({
        data: MOCK_FLOORS_BY_BUILDING,
      });
    }
    if (PIPELINES_BY_SITE.test(url)) {
      return Promise.resolve({
        data: MOCK_PIPELINES_BY_SITE,
      });
    }
    if (FOLDER.test(url)) {
      return Promise.resolve({
        data: MOCK_FOLDER,
      });
    }
    if (FOLDER_FILES.test(url)) {
      return Promise.resolve({
        data: [],
      });
    }
  }),
  create: jest.fn(function () {
    return this;
  }),
  interceptors: { request: { use: jest.fn() } },
};
