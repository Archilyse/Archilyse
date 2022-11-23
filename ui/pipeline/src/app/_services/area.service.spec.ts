import { defaultOrBase, MockApiService } from './api.service.mock';
import { AreaService } from './area.service';
import { EditorService } from './editor.service';
import { FloorplanValidationService } from './floorplan/floorplan.validation.service';
import * as footprint from '../_shared-assets/http_request_simpleBrooks.json';
import { EditorConstants } from '../_shared-libraries/EditorConstants';
const brooksModel = defaultOrBase(footprint);

describe('Area service', function () {
  it('should return all the area id-area_type pairs for a given plan.', async () => {
    const planId = '1';
    const service = new AreaService(new MockApiService(), new EditorService());
    await service.setReferenceBrooksModel(planId, brooksModel);
    const areaTypes = service.getAreaTypes(planId);
    expect(areaTypes.length).toBe(1);
    expect(areaTypes[0].area_type).toBe('KITCHEN_DINING');
  });

  it('should return a dictionary id:area_type with all the plans for a given planId', async () => {
    const planId = '1';
    const service = new AreaService(new MockApiService(), new EditorService());
    await service.setReferenceBrooksModel(planId, brooksModel);
    const areaTypesDict = service.getAreaTypesDict(planId);
    expect(areaTypesDict[111]).toBe('KITCHEN_DINING');
  });

  it('should get an array of Area Ids and returns an array of Mesh uids', async () => {
    const planId = '1';
    const service = new AreaService(new MockApiService(), new EditorService());
    await service.setReferenceBrooksModel(planId, brooksModel);
    const areaIds = [111];
    const meshIds = service.mapAreaIdToMeshId(areaIds);
    expect(meshIds.length).toBe(1);
    expect(meshIds[0]).toBe('f0489b88-0abb-11ea-b008-0242ac120003');
  });

  it('should return the Area Db entity that matches to the given floor and the areaMeshId ', async () => {
    const planId = '1';
    const service = new AreaService(new MockApiService(), new EditorService());
    await service.setReferenceBrooksModel(planId, brooksModel);
    const floorNr = EditorConstants.DEFAULT_FLOOR;
    const areaMeshId = 'f0489b88-0abb-11ea-b008-0242ac120003';
    const areaInfo = service.getAreaInfo(floorNr, areaMeshId);
    expect(areaInfo.area_type).toBe('KITCHEN_DINING');
  });

  it('should return the Area Mesh information given the Area Id', async () => {
    const planId = '1';
    const service = new AreaService(new MockApiService(), new EditorService());
    await service.setReferenceBrooksModel(planId, brooksModel);
    const areaId = '111';
    const areaInfo = service.getAreaByAreaId(areaId);
    expect(areaInfo.id).toBe('f0489b88-0abb-11ea-b008-0242ac120003');
  });

  it('should get the area mesh type', async () => {
    const planId = '1';
    const service = new AreaService(new MockApiService(), new EditorService());
    await service.setReferenceBrooksModel(planId, brooksModel);
    const mockMesh = {
      id: 'f0489b88-0abb-11ea-b008-0242ac120003',
      floorNr: EditorConstants.DEFAULT_FLOOR,
    };
    const areaType = service.getAreaTypeByElement(mockMesh);
    expect(areaType).toBe('KITCHEN_DINING');
  });

  it('should se set the type for a floorNr and a Mesh Area id', async () => {
    const planId = '1';
    const service = new AreaService(new MockApiService(), new EditorService());
    await service.setReferenceBrooksModel(planId, brooksModel);
    const floorNr = EditorConstants.DEFAULT_FLOOR;
    const areaMeshId = 'f0489b88-0abb-11ea-b008-0242ac120003';
    const originalType = 'ROOM';
    const storedTypeBefore = service.getAreaInfo(floorNr, areaMeshId).area_type;
    service.setAreaType(floorNr, areaMeshId, originalType);
    const storedType = service.getAreaInfo(floorNr, areaMeshId).area_type;
    expect(storedTypeBefore).not.toBe(originalType);
    expect(storedType).toBe(originalType);
  });

  it('should find recursively the area and its parent for the given areaId', async () => {
    const planId = '1';
    const service = new AreaService(new MockApiService(), new EditorService());
    await service.setReferenceBrooksModel(planId, brooksModel);
    const areaList = [];
    const position = [0, 0];
    service.getBrooksModelAreas(areaList, position, brooksModel);

    expect(areaList.length).toBe(1);
    expect(areaList[0].type).toBe('AreaType.NOT_DEFINED');
  });
});
