/**
 * This values render text properly.
 * Calculated out of experimentation.
 * @param areaSurface
 */
export function getTextSizeForAreas(areaSurface) {
  let textSize = 1;
  if (areaSurface > 100000) {
    textSize = 200;
  } else if (areaSurface > 10000) {
    textSize = 100;
  } else if (areaSurface > 1000) {
    textSize = 30;
  } else if (areaSurface > 10) {
    textSize = 1;
  }
  return textSize;
}
