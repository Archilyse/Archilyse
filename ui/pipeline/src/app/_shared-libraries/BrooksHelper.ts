import { EditorConstants, isAnArea, isPostArea } from './EditorConstants';
import { COOR_X, COOR_Y } from './SimData';
import * as d3 from 'd3';

export class BrooksHelper {
  public static getHumanType(originalType: string) {
    // We remove the the "PostDynamicAreaTypes." or the "AreaType."
    const prefixLength = isPostArea(originalType) ? 12 : 9;
    return originalType.substr(prefixLength, originalType.length - prefixLength);
  }
  public static humanToType(humanType: string) {
    return `AreaType.${humanType}`;
  }

  public static getAreaData(areaTypeStructure) {
    const keyStructure = Object.keys(areaTypeStructure);
    const areaTypes = [
      {
        type: EditorConstants.AREA_NOT_DEFINED,
        order: -1,
        color: null,
      },
    ];
    keyStructure.forEach(key => {
      const value = areaTypeStructure[key];
      if (!value.children || !value.children.length) {
        areaTypes.push({
          type: key,
          order: value.sort_order,
          color: value.color_code,
        });
      }
    });
    return areaTypes.sort((a, b) => a.order - b.order);
  }

  public static getAreaTypes(areaData) {
    return areaData.map(val => BrooksHelper.getHumanType(val.type));
  }
  public static getAreaColors(areaData) {
    return areaData.filter(val => val.color !== null).map(val => val.color);
  }

  public static getAreaLevelStructure(type, areaTypeStructure) {
    const levels = [];
    this.getAreaLevelStructureRecursive(levels, type, areaTypeStructure);
    return levels;
  }

  public static getAreaLevelStructureRecursive(levels, type, areaTypeStructure) {
    const aTypes = Object.keys(areaTypeStructure);
    aTypes.forEach(aType => {
      const children = areaTypeStructure[aType].children;
      if (children && children.length) {
        if (children.includes(type)) {
          levels.push(aType);
          this.getAreaLevelStructureRecursive(levels, aType, areaTypeStructure);
        }
      }
    });
  }

  public static orderKeys(keyStructure, areaTypeStructure) {
    return keyStructure.sort((keyA, keyB) => {
      const valA = areaTypeStructure[keyA];
      const valB = areaTypeStructure[keyB];

      if (valA.level < valB.level) {
        return -1;
      }
      if (valA.level > valB.level) {
        return 1;
      }
      if (valA.level === valB.level) {
        if (valA.sort_order && valB.sort_order) {
          if (valA.sort_order < valB.sort_order) {
            return -1;
          }
          if (valA.sort_order > valB.sort_order) {
            return 1;
          }
        }
      }
      return 0;
    });
  }

  public static getAreaLevels(areaTypeStructure, min_area_level = 2) {
    const keyStructureOriginal = Object.keys(areaTypeStructure);
    const keyStructure = this.orderKeys(keyStructureOriginal, areaTypeStructure);

    const levels = [];
    keyStructure.forEach(key => {
      const value = areaTypeStructure[key];
      if (value.level === min_area_level) {
        levels.push({ val: key, name: this.getHumanType(key), level: 1 });
        this.getAreaLevelsRecursive(levels, areaTypeStructure, value.children, 2);
      }
    });
    return levels;
  }

  public static getAreaLevelsRecursive(levels, areaTypeStructure, unorderedKeys, level) {
    const keys = this.orderKeys(unorderedKeys, areaTypeStructure);
    if (keys && keys.length) {
      keys.forEach(key => {
        const value = areaTypeStructure[key];
        if (value.children && value.children.length) {
          levels.push({
            level,
            val: key,
            name: this.getHumanType(key),
          });
          this.getAreaLevelsRecursive(levels, areaTypeStructure, value.children, level + 1);
        }
      });
    }
    return levels;
  }

  /**
   * Provided a representative point we search for the area matching
   * @param modelStructure
   * @param representativePoint - The a point inside the area we're looking for
   */
  public static getAreaByPoint(modelStructure, representativePoint) {
    return this.getAreaByPointRecursive(modelStructure, representativePoint, 0, 0);
  }

  /**
   * We search recursively through the brooks model for the specified area.
   * The Ref coordinates is a calculation of the global brooks element position
   * @param brooksElement
   * @param representativePoint - The a point inside the area we're looking for
   * @param refX - Global coordinate X
   * @param refY - Global coordinate Y
   */
  public static getAreaByPointRecursive(brooksElement, representativePoint, refX, refY) {
    if (brooksElement) {
      let deltaX = 0;
      let deltaY = 0;

      // Only if it's a space
      if (brooksElement.position) {
        deltaX = brooksElement.position.coordinates[COOR_X];
        deltaY = brooksElement.position.coordinates[COOR_Y];
      }

      // Is an area, we check if it's the one we're looking for
      if (isAnArea(brooksElement.type)) {
        // representativePoint
        const outerPerimeter = this.makeCoordsGlobal(
          brooksElement.footprint.coordinates[0],
          refX + deltaX,
          refY + deltaY
        );

        let isInside = d3.polygonContains(outerPerimeter, representativePoint);

        for (let i = 1; isInside && i < brooksElement.footprint.coordinates.length; i += 1) {
          const innerPerimeter = this.makeCoordsGlobal(
            brooksElement.footprint.coordinates[i],
            refX + deltaX,
            refY + deltaY
          );
          isInside = isInside && !d3.polygonContains(innerPerimeter, representativePoint);
        }

        if (isInside) {
          return brooksElement;
        }
      }

      // If the element has children we keep on watching recursively.
      // The current position of the element is applied to the children
      if (brooksElement.children) {
        for (let i = 0; i < brooksElement.children.length; i += 1) {
          const child = brooksElement.children[i];
          const result = this.getAreaByPointRecursive(child, representativePoint, refX + deltaX, refY + deltaY);
          if (result) {
            return result;
          }
        }
      }
    }

    return null;
  }

  public static makeCoordsGlobal(coords, deltaX, deltaY) {
    return coords.map(coor => [coor[COOR_X] + deltaX, coor[COOR_Y] + deltaY]);
  }
}
