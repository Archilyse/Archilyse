import { Scene } from '../../types';
import json from './mockScene.json';
import { MOCK_AREA } from '.';
//@ts-ignore
json.layers['layer-1'].areas = { [MOCK_AREA.id]: MOCK_AREA };
export default (json as unknown) as Scene;
