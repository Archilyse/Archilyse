import { capitalize } from 'archilyse-ui-components';

export default room => `${capitalize(room.area_type?.toLowerCase().replace(/_/g, ' '))} ${room.id}`;
