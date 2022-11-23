import { Building } from 'archilyse-ui-components';
import UPLOAD_STATUS from './UploadStatus';

type UploadingFloor = {
  status: UPLOAD_STATUS;
  data: {
    building_id: Building['id'];
    floor_lower_range: string;
    floor_upper_range: string;
    floorplan: FileList;
  };
  error?: any; // @TODO
};

export default UploadingFloor;
