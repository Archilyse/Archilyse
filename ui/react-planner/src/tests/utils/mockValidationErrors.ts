import { ValidationError } from '../../types';

const MOCK_ERROR_LIST: ValidationError[] = [
  {
    is_blocking: 1,
    object_id: '6c2912b25c024bbfa39061d6a1972d8c',
    position: {
      coordinates: [843.46, 853.76],
      type: 'Point',
    },
    text: 'Space not accessible. It should have a type of door, stairs or an elevator',
    type: 'SPACE_NOT_ACCESSIBLE',
  },
  {
    is_blocking: 0,
    object_id: '6588eedc99934fb9bb861e58746af10f',
    position: {
      coordinates: [1262.39, 258.53],
      type: 'Point',
    },
    text: 'Payasos located',
    type: 'WARNING_ANALYSE_PAYASOS',
  },
  {
    is_blocking: 1,
    object_id: 'c096d986d74c4df4998f6e5cfe008551',
    position: {
      coordinates: [348.32, 868.54],
      type: 'Point',
    },
    text: 'Space not accessible. It should have a type of door, stairs or an elevator',
    type: 'SPACE_NOT_ACCESSIBLE',
  },
];

export default MOCK_ERROR_LIST;
