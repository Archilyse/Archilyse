import { HereTileProvider, WebTileDataSource } from '@here/harp-webtile-datasource';
import { APIFormat, AuthenticationMethod, OmvDataSource } from '@here/harp-omv-datasource';
import { OmvTileDecoder } from '@here/harp-omv-datasource/index-worker';
import C from '../../../constants';
import { SIMULATION_MODE } from '../../../types';

const TILES_BY_MODE = {
  [SIMULATION_MODE.SATELLITE]: HereTileProvider.TILE_AERIAL_SATELLITE,
  [SIMULATION_MODE.NORMAL]: HereTileProvider.TILE_BASE_NORMAL,
  [SIMULATION_MODE.HYBRID]: HereTileProvider.TILE_AERIAL_HYBRID,
  [SIMULATION_MODE.TRAFFIC]: HereTileProvider.TILE_TRAFFIC_NORMAL,
};

export class DataSource {
  /**
   * Based on the simType we configure the proper map source.
   * More about DataSources: https://www.harp.gl/docs/master/doc/modules/harp_features_datasource.html
   */
  static setUpDataSource(map, simType: SIMULATION_MODE) {
    // map always has base data source on the first position, we search for the second
    if (map && map.dataSources && map.dataSources.length > 1) {
      const [_, customDataSource] = map.dataSources;
      map.removeDataSource(customDataSource);
      map.update();
    }

    if (simType === SIMULATION_MODE.PLAIN || simType === SIMULATION_MODE.DASHBOARD) return null;

    let newMapSource = null;

    if (TILES_BY_MODE[simType]) {
      newMapSource = new WebTileDataSource({
        name: 'webtile',
        dataProvider: new HereTileProvider({
          tileBaseAddress: TILES_BY_MODE[simType],
          apikey: C.HARPGL_ACCESS_TOKEN,
        }),
      });
    } else {
      newMapSource = new OmvDataSource({
        baseUrl: C.HARPGL_3D_TILES,
        apiFormat: APIFormat.XYZOMV,
        styleSetName: 'tilezen',
        authenticationCode: C.HARPGL_ACCESS_TOKEN,
        authenticationMethod: {
          method: AuthenticationMethod.QueryString,
          name: 'apikey',
        },
        decoder: new OmvTileDecoder(),
      });
    }

    map.addDataSource(newMapSource);
    map.update();

    return newMapSource;
  }
}
