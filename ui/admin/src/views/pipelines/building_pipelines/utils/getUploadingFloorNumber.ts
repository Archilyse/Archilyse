import UploadingFloor from '../types/UploadingFloor';

const getUploadingFloorNumber = (data: UploadingFloor['data']) =>
  data.floor_upper_range !== data.floor_lower_range
    ? `${data.floor_lower_range} - ${data.floor_upper_range}`
    : data.floor_lower_range;

export default getUploadingFloorNumber;
