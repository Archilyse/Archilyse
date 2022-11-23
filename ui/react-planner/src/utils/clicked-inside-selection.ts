import hasCopyPasteBeenDragged from './has-copy-paste-been-dragged';

export default (x, y, selection) => {
  const { startPosition, endPosition, draggingPosition } = selection;
  if (!startPosition || startPosition.x === -1) return false;

  const hasBeenDragged = hasCopyPasteBeenDragged(draggingPosition);

  let minX = Math.min(startPosition.x, endPosition.x);
  let maxX = Math.max(startPosition.x, endPosition.x);
  let minY = Math.min(startPosition.y, endPosition.y);
  let maxY = Math.max(startPosition.y, endPosition.y);

  if (hasBeenDragged) {
    const deltaX = draggingPosition.x - minX;
    const deltaY = draggingPosition.y - minY;

    minX += deltaX;
    minY += deltaY;
    maxX += deltaX;
    maxY += deltaY;
  }
  if (x > minX && x < maxX && y > minY && y < maxY) return true;
  return false;
};
