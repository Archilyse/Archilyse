import { CameraControls } from './CameraControls';
import { COOR_LAT, COOR_LONG } from './SimConstants';

it('camera controls change the position correctly', () => {
  const cameraControls = new CameraControls(null);
  cameraControls.setPosition([10, 11]);

  expect(cameraControls.camPosition[COOR_LONG]).toBe(10);
  expect(cameraControls.camPosition[COOR_LAT]).toBe(11);
});

it('camera handles key left and right', () => {
  const cameraControls = new CameraControls(null);

  const KEY_LEFT = 37;
  const KEY_RIGHT = 39;

  expect(cameraControls.rotateDirection).toBe(0);
  expect(cameraControls.rotateInterval).toBe(null);
  cameraControls.handleKeyDown({
    keyCode: KEY_LEFT,
  });
  expect(cameraControls.rotateDirection).toBeLessThan(0);
  expect(cameraControls.rotateInterval).not.toBe(null);
  cameraControls.handleKeyUp();

  expect(cameraControls.rotateDirection).toBe(0);
  expect(cameraControls.rotateInterval).toBe(null);

  cameraControls.handleKeyDown({
    keyCode: KEY_RIGHT,
  });

  expect(cameraControls.rotateDirection).toBeGreaterThan(0);
  expect(cameraControls.rotateInterval).not.toBe(null);

  cameraControls.handleKeyUp();

  expect(cameraControls.rotateDirection).toBe(0);
  expect(cameraControls.rotateInterval).toBe(null);
});
