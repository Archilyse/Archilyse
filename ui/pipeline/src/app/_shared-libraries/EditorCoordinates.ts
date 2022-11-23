export class EditorCoordinates {
  /**
   * Draws a rectangle given horizontal and vertical coordinates
   * @param dX
   * @param dY
   */
  public static rectangle(dX, dY) {
    const dX2 = dX / 2;
    const dY2 = dY / 2;
    const point00 = [-dX2, -dY2];
    const point01 = [dX2, -dY2];
    const point10 = [dX2, dY2];
    const point11 = [-dX2, dY2];
    const pointEnd = [-dX2, -dY2];
    return [point00, point01, point10, point11, pointEnd];
  }
}
