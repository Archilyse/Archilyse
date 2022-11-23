import { MeshPhongMaterial } from 'three-full/builds/Three.es.js';

export const textMaterial = new MeshPhongMaterial({
  color: 0x444444,
  emissive: 0x444444,
  transparent: false,
});
export const textErrorMaterial = new MeshPhongMaterial({
  color: 0xff0000,
  emissive: 0xff0000,
  transparent: false,
});

export const errorMaterial = new MeshPhongMaterial({
  color: 0xff0000,
  emissive: 0xff0000,
  opacity: 0.4,
  transparent: true,
});

export const errorHighlightMaterial = new MeshPhongMaterial({
  color: 0x0000ff,
  emissive: 0x0000ff,
  opacity: 0.4,
  transparent: true,
});
