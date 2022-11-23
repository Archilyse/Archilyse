const keyClipboard = 'clipboard';
const keyApiToken = 'api_token';
const keyApiRole = 'api_role';
const keyRequestedSims = 'requested_sims';
const keyBuildingStructure = 'building_structure';

export class LocalStorage {
  /*** GLOBAL METHODS */

  public static storeSomething(key: string, data) {
    localStorage.setItem(key, JSON.stringify(data));
  }
  public static getSomething(key: string) {
    const result = localStorage.getItem(key);
    if (result) {
      return JSON.parse(result);
    }
    return null;
  }
  public static removeSomething(key: string) {
    return localStorage.removeItem(key);
  }
  public static removeAll() {
    return localStorage.clear();
  }

  /*** COPY METHODS */

  public static storeClipboard(data) {
    LocalStorage.storeSomething(keyClipboard, data);
  }
  public static getClipboard() {
    return LocalStorage.getSomething(keyClipboard);
  }

  /*** 3dView METHODS */

  public static storeBuildingModelStructure(building, site_id, building_id) {
    LocalStorage.storeSomething(keyBuildingStructure, {
      site_id,
      building_id,
      time: new Date().getTime(),
      data: building,
    });
  }
  public static getBuildingModelStructure(site_id, building_id) {
    const time_to_store = 3600000; // 60*60*1000 1h
    const now = new Date().getTime();
    const result = LocalStorage.getSomething(keyBuildingStructure);
    if (result && result.time && now - result.time < time_to_store) {
      // Same site and same building
      if (result.site_id && result.site_id === site_id) {
        if (result.building_id && result.building_id === building_id) {
          return result.data;
        }
      }
    }
    return null;
  }

  /*** VIEW METHODS */

  public static storeApiRoles(roles: string[]) {
    LocalStorage.storeSomething(keyApiRole, roles);
  }
  public static getApiRoles(): string[] {
    return LocalStorage.getSomething(keyApiRole);
  }
  public static deleteApiRoles() {
    return LocalStorage.removeSomething(keyApiRole);
  }

  public static storeApiToken(token: string) {
    LocalStorage.storeSomething(keyApiToken, token);
  }
  public static getApiToken(): string {
    return LocalStorage.getSomething(keyApiToken);
  }
  public static deleteApiToken() {
    return LocalStorage.removeSomething(keyApiToken);
  }

  public static storeRequestedSims(data) {
    LocalStorage.storeSomething(keyRequestedSims, data);
  }
  public static getRequestedSims() {
    return LocalStorage.getSomething(keyRequestedSims);
  }
}
