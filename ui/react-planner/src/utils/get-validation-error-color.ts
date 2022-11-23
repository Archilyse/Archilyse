import { COLORS } from '../constants';

export default (isBlocking, objectId, highlightedError) => {
  if (objectId === highlightedError) return COLORS.PRIMARY_COLOR;
  if (isBlocking) return 'red';
  return 'yellow';
};
