import { isAnArea } from './EditorConstants';
import { EditorMath } from './EditorMath';
import { AreaService } from '../_services/area.service';

export class EditorAnalysis {
  /**
   * Given a model_structure dives back an analysis object with data about the model structure.
   * @param model
   * @param areaService
   * @param areaTypes
   */
  public static analyzeModelStructure(model, areaService: AreaService, areaTypes) {
    const analysis = {};

    areaTypes.forEach(areaType => {
      analysis[areaType] = [];
    });

    if (model && model.children) {
      EditorAnalysis.analyzeModelStructureRecursive(model.children, analysis, areaService, areaTypes);
    }
    return analysis;
  }

  /**
   * Helper method for the recursive analysis of analyzeModelStructure
   * @param elements
   * @param analysis
   * @param areaService
   * @param areaTypes
   */
  public static analyzeModelStructureRecursive(elements, analysis, areaService: AreaService, areaTypes) {
    if (elements) {
      elements.forEach(element => {
        if (isAnArea(element.type)) {
          const elType = areaService.getAreaTypeByElement(element);
          let found = false;
          for (let i = 0; i < areaTypes.length; i += 1) {
            const type = areaTypes[i];
            if (elType === type) {
              analysis[type].push(EditorAnalysis.calculateAreaElement(element));
              found = true;
              break;
            }
          }
          if (!found) {
            console.error('Area type not found: ', element.type);
          }
        }

        EditorAnalysis.analyzeModelStructureRecursive(element.children, analysis, areaService, areaTypes);
      });
    }
  }

  /**
   * Given an element from the model structure calculates the area in m2
   * @param element
   */
  public static calculateAreaElement(element) {
    return EditorMath.calculateAreaFromPolygon(element.footprint);
  }
}
