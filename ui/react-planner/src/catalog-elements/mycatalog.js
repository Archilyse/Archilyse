import { Catalog } from '../export';

import * as Areas from './areas/export';
import * as Lines from './lines/export';
import * as Holes from './holes/export';
import * as Items from './items/export';

const catalog = new Catalog();

for (const x in Areas) catalog.registerElement(Areas[x]);
for (const x in Lines) catalog.registerElement(Lines[x]);
for (const x in Holes) catalog.registerElement(Holes[x]);
for (const x in Items) catalog.registerElement(Items[x]);

export default catalog;
