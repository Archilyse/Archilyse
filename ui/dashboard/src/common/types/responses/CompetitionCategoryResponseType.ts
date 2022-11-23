export type CompetitionBaseCategoryResponseType = {
  key: string;
  name: string;
};

export type CompetitionMainCategoryResponseType = {
  sub_sections: CompetitionSubSectionResponseType[];
} & CompetitionBaseCategoryResponseType;

export type CompetitionSubSectionResponseType = {
  sub_sections: CompetitionItemResponseType[];
} & CompetitionBaseCategoryResponseType;

export type CompetitionItemResponseType = {
  info?: string;
  red_flag?: boolean;
  unit?: string;
  archilyse?: boolean;
  uploaded?: boolean;
} & CompetitionBaseCategoryResponseType;
