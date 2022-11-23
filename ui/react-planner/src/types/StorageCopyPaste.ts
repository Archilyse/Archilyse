import Hole from './Hole';
import Item from './Item';
import Line from './Line';
import Selection from './Selection';
import Vertex from './Vertex';

type StorageCopyPaste = {
  elements: {
    lines: Line[];
    items: Item[];
    holes: Hole[];
    vertices: Vertex[];
  };
  selection: Selection;
  planId: number;
};

export default StorageCopyPaste;
