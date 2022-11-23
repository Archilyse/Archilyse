import BaseModel from './Base';
import ClassificationsSchemas from './Classifications';
import TaskStatus from './TaskStatus';

type BasicFeatureError = {
  type: string;
  human_id: string;
  position: {
    type: string;
    coordinates: [number, number];
  };
  object_id: number;
  text: string;
};

type QAValidation = {
  [key: string]: string[];
};

type SiteModel = {
  name: string;
  client_site_id?: string;
  region: string;
  lat: number;
  lon: number;
  site_plan_file?: string;
  raw_dir?: string;
  client_id: number;

  currently_assigned: boolean;
  full_slam_results: TaskStatus;
  pipeline_and_qa_complete: boolean;
  heatmaps_qa_complete: boolean;
  basic_features_status: TaskStatus;
  basic_features_error?: { errors: (BasicFeatureError | null)[] };
  qa_validation?: QAValidation;
  validation_notes?: string;
  priority: number;
  delivered?: boolean;

  gcs_buildings_link?: string;
  gcs_json_surroundings_link?: string;
  gcs_ifc_link?: string;
  group_id?: number;
  classification_scheme: ClassificationsSchemas;

  ifc_import_status?: string;
  ifc_import_exceptions?: string;
} & BaseModel;

export default SiteModel;
