import { CompetitionMainCategoryResponseType } from '../../../common/types';

const categories: CompetitionMainCategoryResponseType[] = [
  {
    key: 'architecture_usage',
    name: 'Architecture Overview',
    sub_sections: [
      {
        name: 'Residential Share',
        key: 'residential_share',
        sub_sections: [
          {
            name: 'Evaluation residential use',
            key: 'evaluation_residential_use',
            info: 'Some message that describes meaning of the data feature',
            archilyse: true,
          },
        ],
      },
    ],
  },
  {
    name: 'Architecture Programme',
    key: 'architecture_room_programme',
    sub_sections: [
      {
        name: 'Generosity',
        key: 'generosity',
        sub_sections: [
          {
            name: 'Calculation of the open space over the largest possible square.',
            key: 'open_space_over_largest_possible_square',
            info: 'The generosity of the open space within a unit',
          },
          {
            name: 'Manual input of number of kitchen elements.',
            key: 'manual_input_of_kitchen_elements',
            red_flag: true,
          },
        ],
      },
    ],
  },
];

export default categories;
