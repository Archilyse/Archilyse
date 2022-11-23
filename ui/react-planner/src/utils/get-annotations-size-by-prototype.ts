const getAnnotationsSizeByPrototype = ({ state }) => {
  const selectedLayer = state.scene.selectedLayer;
  const areasSize = state.scene.layers[selectedLayer].selected.areas.length;

  const selectedLines = state.scene.layers[selectedLayer].selected.lines;
  const linesSize = selectedLines.length;

  const selectedHoles = state.scene.layers[selectedLayer].selected.holes;
  const holesSize = selectedHoles.length;

  const selectedItems = state.scene.layers[selectedLayer].selected.items;
  const itemsSize = selectedItems.length;

  // check if only lines or holes or items are selected
  const prototypesSelected = [linesSize, holesSize, itemsSize, areasSize].filter(s => s > 0).length;
  const onlyOnePrototypeSelected = prototypesSelected === 1;

  return {
    selectedLines,
    linesSize,
    selectedHoles,
    holesSize,
    selectedItems,
    itemsSize,
    onlyOnePrototypeSelected,
  };
};

export default getAnnotationsSizeByPrototype;
