import DMSItem from './DMSItem';

type OpenedFile = DMSItem & {
  size: number;
  updated: string;
  comments: { id: 'number'; creator: { name: string }; comment: string; created: Date }[];
};
export default OpenedFile;
