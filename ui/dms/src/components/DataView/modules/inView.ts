import { C } from 'Common';

const { DMS_VIEWS } = C;

type DmsView = typeof DMS_VIEWS[keyof typeof DMS_VIEWS];

export default (urlArray: DmsView[], pathname: DmsView | string) => urlArray.some(url => pathname === url);
