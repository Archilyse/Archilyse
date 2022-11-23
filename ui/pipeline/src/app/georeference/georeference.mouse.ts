import { Pointer as PointerInteraction } from 'ol/interaction';

/**
 * This code wa taken from:
 * https://openlayers.org/en/latest/examples/custom-interactions.html
 */

export const Drag = /*@__PURE__*/ (function (PointerInteraction) {
  // tslint:disable-next-line:function-name
  function Drag(onStart, onEnd) {
    PointerInteraction.call(this, {
      handleDownEvent,
      handleDragEvent,
      handleMoveEvent,
      handleUpEvent,
    });

    this.onStart_ = onStart;
    this.onEnd_ = onEnd;

    /**
     * @type {import("../src/ol/coordinate.js").Coordinate}
     * @private
     */
    this.coordinate_ = null;

    /**
     * @type {string|undefined}
     * @private
     */
    this.cursor_ = 'pointer';

    /**
     * @type {Feature}
     * @private
     */
    this.feature_ = null;

    /**
     * @type {string|undefined}
     * @private
     */
    this.previousCursor_ = undefined;
  }

  if (PointerInteraction) {
    Drag.__proto__ = PointerInteraction;
  }
  Drag.prototype = Object.create(PointerInteraction && PointerInteraction.prototype);
  Drag.prototype.constructor = Drag;

  return Drag;
})(PointerInteraction);

/**
 * Drag start
 * @param evt
 * @return {boolean} `true` to start the drag sequence.
 */
function handleDownEvent(evt) {
  const map = evt.map;

  const feature = map.forEachFeatureAtPixel(evt.pixel, feature => {
    return feature;
  });

  if (feature) {
    if (feature.getId() !== 'georeferencedBuilding') {
      return false;
    }
    this.coordinate_ = evt.coordinate;
    this.feature_ = feature;
    this.onStart_(evt);
  }

  return !!feature;
}

/**
 * Dragging event
 * @param evt
 */
function handleDragEvent(evt) {
  if (this.coordinate_ && this.feature_) {
    const deltaX = evt.coordinate[0] - this.coordinate_[0];
    const deltaY = evt.coordinate[1] - this.coordinate_[1];

    if (this.feature_.getGeometry) {
      const geometry = this.feature_.getGeometry();
      geometry.translate(deltaX, deltaY);

      this.coordinate_[0] = evt.coordinate[0];
      this.coordinate_[1] = evt.coordinate[1];
    }
  }
}

/**
 * Mouse move event
 * @param evt
 */
function handleMoveEvent(evt) {
  if (this.cursor_) {
    const map = evt.map;
    const feature = map.forEachFeatureAtPixel(evt.pixel, function (feature) {
      return feature;
    });
    const element = map.getTargetElement();
    if (feature) {
      if (element.style.cursor !== this.cursor_) {
        this.previousCursor_ = element.style.cursor;
        element.style.cursor = this.cursor_;
      }
    } else if (this.previousCursor_ !== undefined && this.previousCursor_ !== null) {
      element.style.cursor = this.previousCursor_;
      this.previousCursor_ = undefined;
    }
  }
}

/**
 * @return {boolean} `false` to stop the drag sequence.
 */
function handleUpEvent(evt) {
  this.onEnd_(evt);

  this.coordinate_ = null;
  this.previousCursor_ = null;
  this.feature_ = null;
  return false;
}
