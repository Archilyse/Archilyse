import { EditorConstants, isAnArea, isASeparator, isASpace, isFurniture } from './EditorConstants';

describe('EditorConstants.ts library', () => {
  beforeEach(() => {});

  it('should identify separators properly', () => {
    expect(isASeparator('AreaType.ROOM')).toBe(false);
    expect(isASeparator('AreaType.BATHROOM')).toBe(false);

    expect(isASeparator('SeparatorType.WALL')).toBe(true);
    expect(isASeparator('SeparatorType.RAILING')).toBe(true);

    expect(isASeparator(EditorConstants.SEPARATOR_NOT_DEFINED)).toBe(true);
    expect(isASeparator(EditorConstants.SEPARATOR_WALL)).toBe(true);
    expect(isASeparator(EditorConstants.RAILING)).toBe(true);
    expect(isASeparator(EditorConstants.ENVELOPE)).toBe(true);
    expect(isASeparator(EditorConstants.COLUMN)).toBe(true);
  });

  it('should identify area types properly', () => {
    expect(isAnArea(null)).toBe(false);
    expect(isAnArea('')).toBe(false);

    expect(isAnArea('AreaType.ROOM')).toBe(true);
    expect(isAnArea('AreaType.BATHROOM')).toBe(true);

    expect(isAnArea('SeparatorType.WALL')).toBe(false);
    expect(isAnArea('FeatureType.ELEVATOR')).toBe(false);
    expect(isAnArea('OpeningType.DOOR')).toBe(false);
  });

  it('should identify spaces properly', () => {
    expect(isASpace(null)).toBe(false);
    expect(isASpace('')).toBe(false);

    expect(isASpace('SeparatorType.WALL')).toBe(false);
    expect(isASpace('FeatureType.ELEVATOR')).toBe(false);
    expect(isASpace('OpeningType.DOOR')).toBe(false);
    expect(isASpace('AreaType.ROOM')).toBe(false);

    expect(isASpace('SpaceType.ROOM')).toBe(true);
  });

  it('should identify furniture properly', () => {
    expect(isFurniture(null)).toBe(false);
    expect(isFurniture('')).toBe(false);

    expect(isFurniture('SeparatorType.WALL')).toBe(false);
    expect(isFurniture('FeatureType.ELEVATOR')).toBe(true);
    expect(isFurniture('OpeningType.DOOR')).toBe(false);
    expect(isFurniture('AreaType.ROOM')).toBe(false);

    expect(isFurniture('SpaceType.ROOM')).toBe(false);

    expect(isFurniture(EditorConstants.DESK)).toBe(true);
    expect(isFurniture(EditorConstants.CHAIR)).toBe(true);
  });
});
