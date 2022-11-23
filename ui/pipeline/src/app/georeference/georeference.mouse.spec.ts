import { Drag } from './georeference.mouse';
import OlMap from 'ol/Map';

describe('Georeference mouse component', () => {
  it('should create an instance', () => {
    function onStart() {}
    function onEnd() {}

    const dragInstance = new Drag(onStart, onEnd);

    const mockEvt = {
      map: new OlMap({}),
      coordinate: [10, 20],
    };

    dragInstance.handleDownEvent(mockEvt);
    // dragInstance.handleDragEvent(mockEvt);
    dragInstance.handleMoveEvent(mockEvt);
    dragInstance.handleUpEvent(mockEvt);

    expect(dragInstance).toBeDefined();
  });
});
