import ProviderHash from '../providers/hash';

/*  @TODO: The hash code here changes everytime a selection changes,
 *  as the layer changes it `selected` List and the selected item, line...etc, update its own `selected` attribute
 */
export default state => {
  const selectedLayer = state.scene.selectedLayer;
  const projectHashCode = ProviderHash.hash(state.scene.layers[selectedLayer]);
  return projectHashCode;
};
