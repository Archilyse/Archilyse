import XYCoord from './XYCoord';

type Selection = {
  startPosition: XYCoord;
  endPosition: XYCoord;
  draggingPosition: XYCoord;
  lines?: string[]; // [id1, id2...]
  items?: string[];
  holes?: string[];
  rotation?: number;
};

export default Selection;
