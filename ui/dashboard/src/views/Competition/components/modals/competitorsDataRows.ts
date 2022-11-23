import { INPUT_TYPES } from 'archilyse-ui-components';
import { RowOptionType } from '../../../../components/EditableTable/EditableTable';

export type UploadedFeaturesBaseRows = {
  subcategory: string;
  item: {
    key: string;
    value: string;
  };
};

const defaultOption = { truthy: 'Yes', falsy: 'No' };
const createBooleanOption = ({ truthy, falsy } = defaultOption): RowOptionType => ({
  placeholder: `${truthy}/${falsy}`,
  type: INPUT_TYPES.dropdown,
  options: [
    { value: 'true', label: truthy },
    { value: 'false', label: falsy },
  ],
  dropdownProps: { MenuProps: { classes: { list: `menu-list-competitiors-raw-data` } } },
  renderTitle: (value: string) => (JSON.parse(value) ? truthy : falsy),
});

export const ROW_OPTION_BY_CATEGORY: Record<string, RowOptionType> = {
  drying_room_size: createBooleanOption(),
  janitor_office_natural_light: createBooleanOption(),
  determining_whether_barrier_free_access_is_guaranteed: createBooleanOption(),
  determining_whether_minimum_dimension_requirements_are_met: createBooleanOption(),
  determining_whether_there_is_a_power_supply: createBooleanOption(),
  prams_bikes_close_to_entrance: createBooleanOption(),
  car_parking_spaces: createBooleanOption(),
  two_wheels_parking_spaces: createBooleanOption(),
  bike_parking_spaces: createBooleanOption(),
  second_basement_available: createBooleanOption(),
  basement_compartment_availability: createBooleanOption(),
  basement_compartment_size_requirement: createBooleanOption(),
  guess_room_size_requirement: createBooleanOption(),
};
