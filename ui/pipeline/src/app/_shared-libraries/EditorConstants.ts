/**
 * Fixed constants used in the editor
 * Movements - for the User controls.
 * Model structure Types - to understand the model structure
 */
export class EditorConstants {
  static SCALE_LINE = 'line';
  static SCALE_POLYGON = 'polygon';

  static COLORS_HEX = [
    0xff1a54,
    0x3cb44b,
    0xffe119,
    0x4769e5,
    0xf58231,
    0xa723cf,
    0x49ffff,
    0xff35f5,
    0xbcf60c,
    0xfabebe,
    0x00bfbf,
    0xe6beff,
    0xd38831,
    0xfffac8,
    0xca0000,
    0xaaffc3,
    0x808000,
    0xffd8b1,
    0x0000ab,
    0x808080,
  ];
  static COLORS = [
    '#ff1a54',
    '#3cb44b',
    '#ffe119',
    '#4769e5',
    '#f58231',
    '#a723cf',
    '#49ffff',
    '#ff35f5',
    '#bcf60c',
    '#fabebe',
    '#00bfbf',
    '#e6beff',
    '#d38831',
    '#fffac8',
    '#ca0000',
    '#aaffc3',
    '#808000',
    '#ffd8b1',
    '#0000ab',
    '#808080',
  ];

  /** A base scale when the scale is not provided, so we don't show pixel values */
  static BASE_SCALE = 0.0001;

  /** Opacity in the editor */

  static OPACITY_DESELECTED = 0.65;
  static OPACITY_SELECTED = 0.85;
  static OPACITY_BACKGROUND = 1;

  /** **********************************************
   * ANNOTATIONS
   */

  static ANNOTATION_WALL = 'walls';
  static ANNOTATION_RAILING = 'railings';
  static ANNOTATION_DOOR = 'doors';
  static ANNOTATION_ENTRANCE_DOOR = 'entrance_doors';
  static ANNOTATION_WINDOW = 'windows';

  /** **********************************************
   * MODEL STRUCTURE TYPES
   */

  /** Collection of areas */
  static UNIT = 'UNIT';
  /** Generic area */
  static AREA = 'AREA';
  /** Wall of the floorplan */
  static WALL = 'WALL';

  /**  **********************************************
   * Features
   * */

  /** Margin distance from controls to objects*/
  static DISTANCE_OBJECT_TO_CONTROLS_IN_PX = 10;

  /** Feature  Toilet  */
  static ELEVATOR = 'FeatureType.ELEVATOR';
  /** Feature  Toilet  */
  static TOILET = 'FeatureType.TOILET';
  /** Feature  Stairs  */
  static STAIRS = 'FeatureType.STAIRS';
  /** Feature  Sink  */
  static SINK = 'FeatureType.SINK';
  /** Feature  Kitchen  */
  static KITCHEN = 'FeatureType.KITCHEN';
  /** Feature  Desk  */
  static DESK = 'FeatureType.DESK';
  /** Feature  Chair  */
  static CHAIR = 'FeatureType.CHAIR';
  /** Feature  Shower  */
  static SHOWER = 'FeatureType.SHOWER';
  /** Feature  Office misc  */
  static OFFICE_MISC = 'FeatureType.OFFICE_MISC';
  /** Feature  Seat  */
  static SEAT = 'FeatureType.SEAT';
  /** Feature  Shaft  */
  static FEATURE_SHAFT = 'FeatureType.SHAFT';
  /** Feature Bathtube  */
  static FEATURE_BATHTUB = 'FeatureType.BATHTUB';

  static FEATURE_RAMP = 'FeatureType.RAMP';
  static FEATURE_CAR_PARKING = 'FeatureType.CAR_PARKING';
  static FEATURE_BIKE_PARKING = 'FeatureType.BIKE_PARKING';
  static FEATURE_BUILT_IN_FURNITURE = 'FeatureType.BUILT_IN_FURNITURE';
  static FEATURE_OFFICE_DESK = 'FeatureType.OFFICE_DESK';
  /** Feature  Misc  */
  static MISC = 'FeatureType.MISC';

  /** **********************************************
   *  Separators
   *  */

  /** Separator Envelope */
  static SEPARATOR_WALL = 'SeparatorType.WALL';
  /** Separator Envelope */
  static ENVELOPE = 'SeparatorType.ENVELOPE';
  /** Separator Railing */
  static RAILING = 'SeparatorType.RAILING';
  /** Separator Column */
  static COLUMN = 'SeparatorType.COLUMN';
  /** Separator not defined */
  static SEPARATOR_NOT_DEFINED = 'SeparatorType.NOT_DEFINED';

  /** **********************************************
   *  OpeningType
   *  */
  static DOOR = 'OpeningType.DOOR';
  static ENTRANCE_DOOR = 'OpeningType.ENTRANCE_DOOR';
  static WINDOW_ENVELOPE = 'OpeningType.WINDOW_ENVELOPE';
  static WINDOW_INTERIOR = 'OpeningType.WINDOW_INTERIOR';
  static WINDOW = 'OpeningType.WINDOW';

  static OPENING_NOT_DEFINED = 'OpeningType.NOT_DEFINED';

  static AREA_START_LEVEL = 0;

  static AREA_NOT_DEFINED = 'AreaType.NOT_DEFINED';

  /** **********************************************
   *  threejs Library elements
   *  */

  static THREEJS_GROUP = 'Group';
  static THREEJS_MESH = 'Mesh';

  // When displaying a floorplan, with would be the FloorId by default (If not provided)
  static DEFAULT_FLOOR = 1;
}

/**
 * Check is the type is a separator
 * @param type
 */
export function isASeparator(type): boolean {
  return (
    type === EditorConstants.SEPARATOR_NOT_DEFINED ||
    type === EditorConstants.SEPARATOR_WALL ||
    type === EditorConstants.RAILING ||
    type === EditorConstants.ENVELOPE ||
    type === EditorConstants.COLUMN
  );
}

export function isPostArea(type): boolean {
  return type.startsWith('SIACategory.');
}
/**
 * Check is the type is an area
 * @param type
 */
export function isAnArea(type): boolean {
  return type ? type.startsWith('AreaType.') || isPostArea(type) : false;
}

export function isASpace(type): boolean {
  return type ? type.startsWith('SpaceType.') : false;
}

export function isFurniture(type): boolean {
  return (
    type === EditorConstants.TOILET ||
    type === EditorConstants.ELEVATOR ||
    type === EditorConstants.FEATURE_SHAFT ||
    type === EditorConstants.FEATURE_BATHTUB ||
    type === EditorConstants.SINK ||
    type === EditorConstants.STAIRS ||
    type === EditorConstants.KITCHEN ||
    type === EditorConstants.DESK ||
    type === EditorConstants.CHAIR ||
    type === EditorConstants.OFFICE_MISC ||
    type === EditorConstants.SEAT ||
    type === EditorConstants.SHOWER ||
    type === EditorConstants.FEATURE_BIKE_PARKING ||
    type === EditorConstants.FEATURE_BUILT_IN_FURNITURE ||
    type === EditorConstants.FEATURE_CAR_PARKING ||
    type === EditorConstants.FEATURE_OFFICE_DESK ||
    type === EditorConstants.FEATURE_RAMP ||
    type === EditorConstants.MISC
  );
}
