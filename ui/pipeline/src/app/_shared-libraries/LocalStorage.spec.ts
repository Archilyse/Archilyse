import { LocalStorage } from './LocalStorage';

const _value = { a: 1, b: 2, c: 'foo' };

function assertEqual(storedValue, referenceValue) {
  expect(storedValue).toBeDefined();
  expect(storedValue).not.toBeNull();

  // Values defined
  expect(storedValue.a).toBeDefined();
  expect(storedValue.b).toBeDefined();
  expect(storedValue.c).toBeDefined();

  expect(storedValue.a).toBe(referenceValue.a);
  expect(storedValue.b).toBe(referenceValue.b);
  expect(storedValue.c).toBe(referenceValue.c);
}

describe('LocalStorage.ts library', () => {
  beforeEach(() => {
    LocalStorage.removeAll();
  });

  it('should be empty by default', () => {
    const key = 'storageKey';
    const storedValue = LocalStorage.getSomething(key);
    expect(storedValue).toBeNull();
  });

  it('should store and recover a value', () => {
    const key = 'storageKey';

    LocalStorage.storeSomething(key, _value);
    const storedValue = LocalStorage.getSomething(key);

    assertEqual(storedValue, _value);
  });

  it('should store and delete an object', () => {
    const key = 'storageKey';

    LocalStorage.storeSomething(key, _value);
    const storedValue = LocalStorage.getSomething(key);
    expect(storedValue).toBeDefined();
    expect(storedValue).not.toBeNull();

    LocalStorage.removeSomething(key);
    const storedValueAfter = LocalStorage.getSomething(key);
    expect(storedValueAfter).toBeNull();
  });

  it('should store and delete a modelStructure', () => {
    const modelStructure = {
      id: 'model_structure',
      children: ['example', 'fake', 'content'],
    };

    const siteId = 1;
    const buildingId = 1;

    LocalStorage.storeBuildingModelStructure(modelStructure, siteId, buildingId);
    const storedModelStructure = LocalStorage.getBuildingModelStructure(siteId, buildingId);

    expect(storedModelStructure).toBeDefined();
    expect(storedModelStructure).not.toBeNull();

    expect(storedModelStructure.id).toBe(modelStructure.id);
    expect(storedModelStructure.children.length).toBe(modelStructure.children.length);
  });

  it('should store an object in the clipboard and recover it', () => {
    LocalStorage.storeClipboard(_value);
    const storedValue = LocalStorage.getClipboard();

    assertEqual(storedValue, _value);
  });

  it('should store an api key', () => {
    const apiToken = 'AN API KEY CODE';
    LocalStorage.storeApiToken(apiToken);

    const storedApiToken = LocalStorage.getApiToken();
    expect(apiToken).toBe(storedApiToken);
  });

  it('should store an api role', () => {
    const apiRoles = ['admin'];
    LocalStorage.storeApiRoles(apiRoles);

    const storedApiRoles = LocalStorage.getApiRoles();
    expect(storedApiRoles[0]).toBe(apiRoles[0]);
  });

  it('should store the simulation requests', () => {
    const simulations = [
      {
        lat: 10,
        long: 10,
        floorNr: 10,
      },
      {
        lat: 11,
        long: 11,
        floorNr: 11,
      },
    ];
    LocalStorage.storeRequestedSims(simulations);
    const storedSims = LocalStorage.getRequestedSims();

    expect(simulations[0].lat).toBe(storedSims[0].lat);
    expect(simulations[0].long).toBe(storedSims[0].long);
    expect(simulations[0].floorNr).toBe(storedSims[0].floorNr);

    expect(simulations[1].lat).toBe(storedSims[1].lat);
    expect(simulations[1].long).toBe(storedSims[1].long);
    expect(simulations[1].floorNr).toBe(storedSims[1].floorNr);
  });

  it('should store an object in the clipboard and recover it', () => {
    LocalStorage.storeClipboard(_value);
    const storedValue = LocalStorage.getClipboard();

    assertEqual(storedValue, _value);
  });
});
