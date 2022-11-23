import { SIMULATION_MODE } from '../../../types';
import { DataSource } from './DataSource';

const mapMock = {
  removeDataSource: mapSource => {},
  setUpDataSource: mapSource => {},
  addDataSource: mapSource => {},
  update: () => {},
};

it('should create a map source DASHBOARD && PLAIN to be null', () => {
  const simType = SIMULATION_MODE.DASHBOARD;
  const newMapSource = DataSource.setUpDataSource(mapMock, simType);
  expect(newMapSource).toBe(null);

  const simType2 = SIMULATION_MODE.PLAIN;
  const newMapSource2 = DataSource.setUpDataSource(mapMock, simType2);
  expect(newMapSource2).toBe(null);
});

it('should create a map source NOT to be null', () => {
  const simType = SIMULATION_MODE.NORMAL;
  const newMapSource = DataSource.setUpDataSource(mapMock, simType);
  expect(newMapSource.name).toBe('webtile');

  const simType2 = SIMULATION_MODE.SATELLITE;
  const newMapSource2 = DataSource.setUpDataSource(mapMock, simType2);
  expect(newMapSource2.name).toBe('webtile');

  const simType3 = SIMULATION_MODE.HYBRID;
  const newMapSource3 = DataSource.setUpDataSource(mapMock, simType3);
  expect(newMapSource3.name).toBe('webtile');

  const simType4 = SIMULATION_MODE.TRAFFIC;
  const newMapSource4 = DataSource.setUpDataSource(mapMock, simType4);
  expect(newMapSource4.name).toBe('webtile');
});
