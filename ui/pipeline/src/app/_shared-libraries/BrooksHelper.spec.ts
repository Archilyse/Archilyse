import { BrooksHelper } from './BrooksHelper';

const areaTypeStructureMock = {};

areaTypeStructureMock['AreaType.ANF'] = {
  children: ['AreaType.BALCONIES', 'AreaType.LOGGIAS'],
  level: 1,
};
areaTypeStructureMock['AreaType.BALCONIES'] = {
  children: ['AreaType.BALCONY'],
  level: 'ArchilyseAreaTreeLevel.PRICEHUBBLE_LEVEL',
};
areaTypeStructureMock['AreaType.BALCONY'] = {
  children: {},
  color_code: 'rgb(255, 225, 25)',
  level: 'ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL',
  sort_order: 3,
};
areaTypeStructureMock['AreaType.BATHROOM'] = {
  children: {},
  color_code: 'rgb(60, 180, 75)',
  level: 'ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL',
  sort_order: 2,
};
areaTypeStructureMock['AreaType.BATHROOMS'] = {
  children: ['AreaType.BATHROOM'],
  level: 'ArchilyseAreaTreeLevel.PRICEHUBBLE_LEVEL',
};
areaTypeStructureMock['AreaType.CORRIDOR'] = {
  children: {},
  color_code: 'rgb(71, 105, 229)',
  level: 'ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL',
  sort_order: 4,
};
areaTypeStructureMock['AreaType.CORRIDORS'] = {
  children: ['AreaType.CORRIDOR'],
  level: 'ArchilyseAreaTreeLevel.PRICEHUBBLE_LEVEL',
};
areaTypeStructureMock['AreaType.DINING'] = {
  children: {},
  color_code: 'rgb(188, 246, 12)',
  level: 'ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL',
  sort_order: 9,
};
areaTypeStructureMock['AreaType.ELEVATOR'] = {
  children: {},
  color_code: 'rgb(250, 190, 190)',
  level: 'ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL',
  sort_order: 10,
};
areaTypeStructureMock['AreaType.ELEVATORS'] = {
  children: ['AreaType.ELEVATOR'],
  level: 'ArchilyseAreaTreeLevel.PRICEHUBBLE_LEVEL',
};
areaTypeStructureMock['AreaType.FF'] = {
  children: ['AreaType.SHAFTS'],
  level: 1,
};
areaTypeStructureMock['AreaType.HNF'] = {
  children: ['AreaType.ROOMS', 'AreaType.BATHROOMS', 'AreaType.SUNROOMS', 'AreaType.KITCHENS', 'AreaType.CORRIDORS'],
  level: 1,
};
areaTypeStructureMock['AreaType.KITCHEN'] = {
  children: {},
  color_code: 'rgb(73, 255, 255)',
  level: 'ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL',
  sort_order: 7,
};
areaTypeStructureMock['AreaType.KITCHENS'] = {
  children: ['AreaType.KITCHEN', 'AreaType.KITCHEN_DINING'],
  level: 'ArchilyseAreaTreeLevel.PRICEHUBBLE_LEVEL',
};
areaTypeStructureMock['AreaType.KITCHEN_DINING'] = {
  children: {},
  color_code: 'rgb(255, 53, 245)',
  level: 'ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL',
  sort_order: 8,
};
areaTypeStructureMock['AreaType.LOGGIA'] = {
  children: {},
  color_code: 'rgb(167, 35, 207)',
  level: 'ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL',
  sort_order: 6,
};
areaTypeStructureMock['AreaType.LOGGIAS'] = {
  children: ['AreaType.LOGGIA'],
  level: 'ArchilyseAreaTreeLevel.PRICEHUBBLE_LEVEL',
};
areaTypeStructureMock['AreaType.NNF'] = {
  children: ['AreaType.STORAGE_ROOMS'],
  level: 1,
};
areaTypeStructureMock['AreaType.ROOM'] = {
  children: {},
  color_code: 'rgb(255, 26, 84)',
  level: 'ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL',
  sort_order: 1,
};
areaTypeStructureMock['AreaType.ROOMS'] = {
  children: ['AreaType.DINING', 'AreaType.ROOM'],
  level: 'ArchilyseAreaTreeLevel.PRICEHUBBLE_LEVEL',
};
areaTypeStructureMock['AreaType.SHAFT'] = {
  children: {},
  color_code: 'rgb(0, 191, 191)',
  level: 'ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL',
  sort_order: 11,
};
areaTypeStructureMock['AreaType.SHAFTS'] = {
  children: ['AreaType.SHAFT'],
  level: 'ArchilyseAreaTreeLevel.PRICEHUBBLE_LEVEL',
};
areaTypeStructureMock['AreaType.STAIRCASE'] = {
  children: {},
  color_code: 'rgb(230, 190, 255)',
  level: 'ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL',
  sort_order: 12,
};
areaTypeStructureMock['AreaType.STAIRCASES'] = {
  children: ['AreaType.STAIRCASE'],
  level: 'ArchilyseAreaTreeLevel.PRICEHUBBLE_LEVEL',
};
areaTypeStructureMock['AreaType.STORAGE_ROOMS'] = {
  children: ['AreaType.STOREROOM'],
  level: 'ArchilyseAreaTreeLevel.PRICEHUBBLE_LEVEL',
};
areaTypeStructureMock['AreaType.STOREROOM'] = {
  children: {},
  color_code: 'rgb(245, 130, 49)',
  level: 'ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL',
  sort_order: 5,
};
areaTypeStructureMock['AreaType.SUNROOMS'] = {
  children: ['AreaType.WINTERGARTEN'],
  level: 'ArchilyseAreaTreeLevel.PRICEHUBBLE_LEVEL',
};
areaTypeStructureMock['AreaType.VF'] = {
  children: ['AreaType.STAIRCASES', 'AreaType.ELEVATORS'],
  level: 1,
};
areaTypeStructureMock['AreaType.WINTERGARTEN'] = {
  children: {},
  color_code: 'rgb(211, 136, 49)',
  level: 'ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL',
  sort_order: 13,
};

describe('BrooksHelper.ts library', () => {
  beforeEach(() => {});

  it('should get the human string out of an area type', () => {
    const humanStr = BrooksHelper.getHumanType('AreaType.ROOM');
    expect(humanStr).toBe('ROOM');
  });

  it('should get the area type out of a human string', () => {
    const areaType = BrooksHelper.humanToType('ROOM');
    expect(areaType).toBe('AreaType.ROOM');
  });

  it('should get the area data out of the structure', () => {
    const areaData = BrooksHelper.getAreaData(areaTypeStructureMock);

    expect(areaData.length).toBe(14);

    // Not defined areas
    expect(areaData[0].type).toBe('AreaType.NOT_DEFINED');
    expect(areaData[0].color).toBe(null);

    // defined area ROOM color Red
    expect(areaData[1].type).toBe('AreaType.ROOM');
    expect(areaData[1].color).toBe('rgb(255, 26, 84)');

    // defined area ROOM color Red
    expect(areaData[2].type).toBe('AreaType.BATHROOM');
    expect(areaData[2].color).toBe('rgb(60, 180, 75)');
  });
  it('should get the area Types  out of the structure', () => {
    const areaData = BrooksHelper.getAreaData(areaTypeStructureMock);
    const areaTypesHuman = BrooksHelper.getAreaTypes(areaData);

    expect(areaTypesHuman.length).toBe(14);

    expect(areaTypesHuman[0]).toBe('NOT_DEFINED');
    expect(areaTypesHuman[1]).toBe('ROOM');
    expect(areaTypesHuman[2]).toBe('BATHROOM');
    expect(areaTypesHuman[3]).toBe('BALCONY');
  });
  it('should get the area colors out of the structure', () => {
    const areaData = BrooksHelper.getAreaData(areaTypeStructureMock);
    const areaColors = BrooksHelper.getAreaColors(areaData);
    expect(areaColors.length).toBe(13);
    expect(areaColors[0]).toBe('rgb(255, 26, 84)');
    expect(areaColors[1]).toBe('rgb(60, 180, 75)');
    expect(areaColors[2]).toBe('rgb(255, 225, 25)');
  });
  it('should get the level Structure out of the area Types', () => {
    const areaType = 'AreaType.ROOM';
    const levelStructure = BrooksHelper.getAreaLevelStructure(areaType, areaTypeStructureMock);
    expect(levelStructure.length).toBe(2);
    expect(levelStructure[0]).toBe('AreaType.ROOMS');
    expect(levelStructure[1]).toBe('AreaType.HNF');

    const areaTypeBal = 'AreaType.BALCONY';
    const levelStructureBal = BrooksHelper.getAreaLevelStructure(areaTypeBal, areaTypeStructureMock);
    expect(levelStructureBal.length).toBe(2);
    expect(levelStructureBal[0]).toBe('AreaType.BALCONIES');
    expect(levelStructureBal[1]).toBe('AreaType.ANF');
  });
});
