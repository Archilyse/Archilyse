import { OpenedFile } from 'Common/types';
import { parseDMSItem } from './parseDMSItem';

export default (file): OpenedFile => ({
  ...parseDMSItem(file, file.content_type),
  size: file.size,
  updated: file.updated,
  comments: file.comments,
});
