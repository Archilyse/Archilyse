import { RequestStatusType } from '../constants';
import Background from './Background';
import FloorScale from './FloorScale';
import XYCoord from './XYCoord';

type PanelScaleProps = {
  points: XYCoord[];
  background: Background;
  paperFormat: string;
  scaleRatio: number;
  scaleTool: any;
  floorScales: FloorScale[];
  floorScalesRequest: typeof RequestStatusType;
  planActions: any;
  projectActions: any;
  scaleAllowed: boolean;
  scaleArea: any;
  stateExtractor: () => void;
};

export default PanelScaleProps;
