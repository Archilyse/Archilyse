import { ProviderHash } from '../providers';
import { HistoryStructure } from '../models';
import { MAX_HISTORY_LIST_SIZE } from '../constants';
import { historyPop, historyPush } from './history';

const getMockItem = (data = {}) => ({ ...data, date: Date.now() });

// @TODO: Use provider hash all along this file
describe('History methods', () => {
  let historyStructure = null;
  let item = null;

  beforeEach(() => {
    item = getMockItem();
    historyStructure = new HistoryStructure(item);
  });

  it('historyPush should add an item to the structure list and update the last item', () => {
    expect(historyStructure.list.length === 0).toBeTruthy();
    console.log(`before historyStructure.list`, historyStructure.list);

    item = getMockItem();
    historyStructure = historyPush(historyStructure, item);
    expect(historyStructure.list.length === 0).toBeFalsy();
    expect(historyStructure.list.length).toEqual(1);
    expect(ProviderHash.hash(historyStructure.last)).toEqual(ProviderHash.hash(item));

    // Also test if historyStructure.list is not updated if the last item is passed as item in historyPush call
    // historyStructure = historyPush(historyStructure, item);
    // expect(historyStructure.list.length).toEqual(1);
  });

  it('historyPop should remove an item from the structure list and update the last item', () => {
    const LAST_ITEM_HASH = ProviderHash.hash(historyStructure.last);
    item = getMockItem();
    historyStructure = historyPush(historyStructure, item);

    expect(historyStructure.list.length === 0).toBeFalsy();

    historyStructure = historyPop(historyStructure);
    expect(historyStructure.list.length === 0).toBeTruthy();
    expect(ProviderHash.hash(historyStructure.last)).toEqual(LAST_ITEM_HASH);
  });

  it(`History list should store max ${MAX_HISTORY_LIST_SIZE} items`, () => {
    for (let i = 0; i < MAX_HISTORY_LIST_SIZE; ++i) {
      const randomNumber = Math.random() * (10000 - i) + i;
      item = getMockItem({ i, randomNumber });
      historyStructure = historyPush(historyStructure, item);
    }
    expect(historyStructure.list.length).toEqual(MAX_HISTORY_LIST_SIZE);

    // Now that the list is full, let's add another item and see if the first one is removed
    const FIRST_ITEM_HASH = ProviderHash.hash(historyStructure.list[0]);
    item = getMockItem();
    historyStructure = historyPush(historyStructure, item);

    expect(historyStructure.list.length).toEqual(MAX_HISTORY_LIST_SIZE);
    expect(ProviderHash.hash(historyStructure.list[0])).not.toEqual(FIRST_ITEM_HASH);
  });
});
