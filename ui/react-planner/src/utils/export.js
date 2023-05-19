import * as GeometryUtils from './geometry';
import * as MathUtils from './math';
import * as SnapUtils from './snap';
import cloneDeep from './clone-deep';
import * as SnapSceneUtils from './snap-scene';
import * as history from './history';
import * as ObjectUtils from './objects-utils';
import IDBroker from './id-broker';
import getValidationErrorColor from './get-validation-error-color';
import NameGenerator from './name-generator';
import getImgDimensions from './get-img-dimensions';
import hasProjectChanged from './has-project-changed';
import getProjectHashCode from './get-project-hash-code';
import debounce from './debounce';
import hasCopyPasteBeenDragged from './has-copy-paste-been-dragged';
import hasCopyPasteFromAnotherPlan from './has-copy-paste-from-another-plan';
import clickedInsideSelection from './clicked-inside-selection';
import * as PolygonUtils from './polygon-utils';
import * as CopyPasteUtils from './copy-paste-utils';
import PostProcessor from './post-processor.ts';
import ProjectHasAnnotations from './project-has-annotations';
import isScaling from './is-scaling';
import getSelectedAnnotationsSize from './get-selected-annotations-size';
import isObjectEmpty from './is-object-empty';
import getFastStateObject from './get-fast-state-object';
import getLabellingPrediction from './get-labelling-prediction';

export {
  CopyPasteUtils,
  cloneDeep,
  getImgDimensions,
  getLabellingPrediction,
  GeometryUtils,
  MathUtils,
  SnapUtils,
  SnapSceneUtils,
  history,
  IDBroker,
  NameGenerator,
  ObjectUtils,
  getValidationErrorColor,
  hasProjectChanged,
  getProjectHashCode,
  debounce,
  PolygonUtils,
  hasCopyPasteFromAnotherPlan,
  hasCopyPasteBeenDragged,
  clickedInsideSelection,
  PostProcessor,
  ProjectHasAnnotations,
  isScaling,
  isObjectEmpty,
  getSelectedAnnotationsSize,
  getFastStateObject,
};

export default {
  CopyPasteUtils,
  cloneDeep,
  getImgDimensions,
  getLabellingPrediction,
  GeometryUtils,
  MathUtils,
  SnapUtils,
  SnapSceneUtils,
  history,
  IDBroker,
  NameGenerator,
  ObjectUtils,
  getValidationErrorColor,
  hasProjectChanged,
  getProjectHashCode,
  debounce,
  PolygonUtils,
  hasCopyPasteBeenDragged,
  clickedInsideSelection,
  hasCopyPasteFromAnotherPlan,
  PostProcessor,
  ProjectHasAnnotations,
  isScaling,
  isObjectEmpty,
  getSelectedAnnotationsSize,
  getFastStateObject,
};
