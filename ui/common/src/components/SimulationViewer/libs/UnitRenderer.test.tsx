import * as THREE from 'three';
import C from '../../../constants';
import { CONTEXT_UNIT_OPACITY, UNIT_OPACITY } from './SimConstants';
import { addEdgesAroundGeometry, getUnitMaterial } from './UnitRenderer';

const { DASHBOARD_3D_UNIT_COLOR, DASHBOARD_3D_EDGES_COLOR, DASHBOARD_3D_EDGES_COLOR_NO_CONTEXT, FADED_UNIT_COLOR } = C;

describe('Unit Renderer', () => {
  const getMockMesh = () => {
    const mockGeometry = new THREE.BufferGeometry();
    const vertices = new Float32Array([1, 10, 5]);
    mockGeometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));

    return new THREE.Mesh(mockGeometry, getUnitMaterial(true));
  };

  describe('getUnitMaterial', () => {
    it('With a context unit it, returns material with grey color high opacity', () => {
      const isContextUnit = true;

      const contextMaterial = getUnitMaterial(isContextUnit);

      const expectedColor = new THREE.Color(DASHBOARD_3D_UNIT_COLOR);
      expect(contextMaterial.color).toStrictEqual(expectedColor);
      expect(contextMaterial.opacity).toBe(CONTEXT_UNIT_OPACITY);
    });
    it('With a non context unit returns material with light grey color & small opacity', () => {
      const isContextUnit = false;

      const contextMaterial = getUnitMaterial(isContextUnit);

      const expectedColor = new THREE.Color(FADED_UNIT_COLOR);
      expect(contextMaterial.color).toStrictEqual(expectedColor);
      expect(contextMaterial.opacity).toBe(UNIT_OPACITY);
    });
  });

  describe('addEdgesAroundGeometry', () => {
    let mesh;

    beforeEach(() => {
      mesh = getMockMesh();
    });

    it('With a context unit it add grey edges with full opacity', () => {
      const isContextUnit = true;

      addEdgesAroundGeometry(mesh, isContextUnit);

      const [modifiedMesh] = mesh.children;
      const expectedColor = new THREE.Color(DASHBOARD_3D_EDGES_COLOR);
      expect(modifiedMesh.material.type).toBe(new THREE.LineBasicMaterial().type);
      expect(modifiedMesh.material.color).toStrictEqual(expectedColor);
    });
    it('With a non context unit, it adds white edges almost transparent', () => {
      const isContextUnit = false;

      addEdgesAroundGeometry(mesh, isContextUnit);

      const [modifiedMesh] = mesh.children;
      const expectedColor = new THREE.Color(DASHBOARD_3D_EDGES_COLOR_NO_CONTEXT);
      expect(modifiedMesh.material.type).toBe(new THREE.LineBasicMaterial().type);
      expect(modifiedMesh.material.color).toStrictEqual(expectedColor);
      expect(modifiedMesh.material.transparent).toStrictEqual(true);
    });
  });
});
