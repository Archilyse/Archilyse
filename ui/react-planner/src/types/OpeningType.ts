import { OPENING_TYPE } from '../constants';

type OpeningType = typeof OPENING_TYPE[keyof typeof OPENING_TYPE];

export default OpeningType;
