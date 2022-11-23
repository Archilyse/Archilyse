import * as THREE from 'three';
import C from '../../../constants';
import { Unit } from '../../../types';
import { CONTEXT_UNIT_OPACITY, HIGHLIGHTED_UNIT_OPACITY, UNIT_OPACITY } from './SimConstants';
import { UnitControls } from './UnitControls';

describe('Unit Controls', () => {
  let unitControls;
  let mockUnit;
  const initialColor = new THREE.Color(C.DASHBOARD_3D_UNIT_COLOR);
  const initialOpacity = CONTEXT_UNIT_OPACITY;
  const mockUnitClientId = 'AnIdRandom123456';

  const createMockUnit = () => ({
    material: {
      color: new THREE.Color(C.DASHBOARD_3D_UNIT_COLOR), // Create a new object color every time to avoid side effects in the tests
      opacity: initialOpacity,
    },
  });

  const createMockMesh = mockUnit => ({
    children: [mockUnit],
  });

  beforeEach(() => {
    unitControls = new UnitControls(null);
    mockUnit = createMockUnit();
    const mockMesh = createMockMesh(mockUnit);
    unitControls.unitToMeshes[mockUnitClientId] = [mockMesh];
  });

  const assertHighlightedUnit = () => {
    const primaryColor = new THREE.Color(C.COLORS.PRIMARY);
    expect(mockUnit.material.color).toStrictEqual(primaryColor);
    expect(mockUnit.material.opacity).toBe(HIGHLIGHTED_UNIT_OPACITY);
  };

  describe('higlightUnits', () => {
    it('highlights a single unit', () => {
      unitControls.highlightUnits([mockUnitClientId]);
      assertHighlightedUnit();
    });
  });

  describe('restoreInitialUnitsStyle', () => {
    it(`re-applies initial style to the context units`, () => {
      unitControls.highlightUnits([mockUnitClientId]);
      assertHighlightedUnit();

      unitControls.restoreInitialUnitsStyle([]);
      expect(mockUnit.material.color).toStrictEqual(initialColor);
      expect(mockUnit.material.opacity).toBe(initialOpacity);
    });

    it(`re-applies initial style to the non-context units`, () => {
      unitControls.highlightUnits([mockUnitClientId]);
      assertHighlightedUnit();

      unitControls.restoreInitialUnitsStyle(['other_unit_which_is_mot_the_mock_one']);

      const nonContextUnitColor = new THREE.Color(C.FADED_UNIT_COLOR);
      expect(mockUnit.material.color).toStrictEqual(nonContextUnitColor);
      expect(mockUnit.material.opacity).toBe(UNIT_OPACITY);
    });

    describe(`areUnitsEqual`, () => {
      it(`check if units are equal`, () => {
        const unitControls = new UnitControls(null);

        const unitsA1 = ['1111'];
        const unitsB1 = ['1111'];
        expect(unitControls.areUnitsEqual(unitsA1, unitsB1)).toBe(true);

        const unitsB2 = ['1112'];
        expect(unitControls.areUnitsEqual(unitsA1, unitsB2)).toBe(false);

        const unitsB3 = null;
        expect(unitControls.areUnitsEqual(unitsA1, unitsB3)).toBe(false);

        const unitsA4 = ['2222', '1111'];
        const unitsB4 = ['1111', '2222'];
        expect(unitControls.areUnitsEqual(unitsA4, unitsB4)).toBe(true);
      });
    });

    describe(`colorizeUnitsByPrice`, () => {
      it(`Colorize units depending on its price`, () => {
        const unit1 = createMockUnit();
        const unit2 = createMockUnit();
        const unit3 = createMockUnit();

        const mockMesh1 = createMockMesh(unit1);
        const mockMesh2 = createMockMesh(unit2);
        const mockMesh3 = createMockMesh(unit3);

        unitControls.unitToMeshes = {
          unit_1: [mockMesh1],
          unit_2: [mockMesh2],
          unit_3: [mockMesh3],
        };

        const mockCurrentUnits: Partial<Unit>[] = [
          { client_id: 'unit_1', ph_final_gross_rent_annual_m2: 0 },
          { client_id: 'unit_2', ph_final_gross_rent_annual_m2: 5 },
          { client_id: 'unit_3', ph_final_gross_rent_annual_m2: 10 },
        ];

        unitControls.colorizeUnitsByPrice(mockCurrentUnits);

        // First unit has low price
        const EXPECTED_COLD_BLUE_COLOR = '2c7bb6';
        expect(unit1.material.color.getHexString()).toBe(EXPECTED_COLD_BLUE_COLOR);

        // Second unit has medium price
        const EXPECTED_WARM_YELLOW_COLOR = 'ffff8c';
        expect(unit2.material.color.getHexString()).toBe(EXPECTED_WARM_YELLOW_COLOR);

        // Third unit has high price
        const EXPECTED_RED_HOT_COLOR = 'd7191c';
        expect(unit3.material.color.getHexString()).toBe(EXPECTED_RED_HOT_COLOR);
      });
    });
  });
});
