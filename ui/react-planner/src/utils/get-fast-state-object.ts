import { current, isDraft, original } from 'immer';
import { State } from '../types';

/* Helper to get the js object with the modifications (current) or the original one
 *  Used to increase perf. on read operations:
 * https://immerjs.github.io/immer/performance/#you-can-always-opt-out
 * https://immerjs.github.io/immer/performance/#for-expensive-search-operations-read-from-the-original-state-not-the-draft
 */
const getFastStateObject = (state: State, options = { returnOriginalObject: false }): State => {
  if (isDraft(state)) {
    return options.returnOriginalObject ? original(state) : current(state);
  }
  return state;
};

export default getFastStateObject;
