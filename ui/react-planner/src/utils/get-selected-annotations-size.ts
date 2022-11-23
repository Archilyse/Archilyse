const getSelectedAnnotationsSize = state => {
  const selectedLayer = state.scene.selectedLayer;
  const { areas, holes, items, lines } = state.scene.layers[selectedLayer].selected;
  const selectedAnnotations = areas.concat(holes, items, lines);
  return selectedAnnotations.length;
};

export default getSelectedAnnotationsSize;
