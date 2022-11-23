export type EntityAreaRecord = {
  id: string;
  netArea: number;
};

export type AreaData = {
  [title: string]: EntityAreaRecord[];
};
