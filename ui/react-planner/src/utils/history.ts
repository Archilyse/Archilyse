import { HistoryStructure, Scene } from '../types';
import cloneDeep from '../utils/clone-deep';
import { MAX_HISTORY_LIST_SIZE } from '../constants';
import { ProviderHash } from '../providers';

export function historyPush(historyStructure: HistoryStructure, scene: Scene): HistoryStructure {
  if (!historyStructure.last) {
    historyStructure.last = cloneDeep(scene);
  } else {
    if (ProviderHash.hash(historyStructure.last) !== ProviderHash.hash(scene)) {
      // @TODO: Use project hash code to avoid this expensive comparison
      historyStructure.list.push(historyStructure.last);
      if (historyStructure.list.length > MAX_HISTORY_LIST_SIZE) {
        historyStructure.list.shift(); // removes first element
      }

      historyStructure.last = cloneDeep(scene);
    }
  }

  return historyStructure;
}
export function historyPop(historyStructure: HistoryStructure): HistoryStructure {
  if (historyStructure.last && historyStructure.list.length) {
    historyStructure.last = cloneDeep(historyStructure.list.pop());
  }

  return historyStructure;
}
