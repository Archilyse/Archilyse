import React from 'react';
import { Icon } from 'archilyse-ui-components';
import { C } from 'Common';

const { MIME_TYPES } = C;

const TYPE_RENDERER = {
  [MIME_TYPES.PDF]: style => <Icon style={style}>picture_as_pdf_outlined</Icon>,
  [MIME_TYPES.JPEG]: style => <Icon style={style}>crop_original</Icon>,
  [MIME_TYPES.PNG]: style => <Icon style={style}>crop_original</Icon>,
  folder: style => <Icon style={style}>folder</Icon>,
  'folder-clients': style => <Icon style={style}>folder_shared</Icon>,
  'folder-sites': style => <Icon style={style}>bar_chart</Icon>,
  'folder-buildings': style => <Icon style={style}>apartment</Icon>,
  'folder-floors': style => <Icon style={style}>layers</Icon>,
  'folder-units': style => <Icon style={style}>dashboard</Icon>,
  'folder-rooms': style => <Icon style={style}>stop</Icon>,
  'custom-folder': style => <Icon style={style}>folder</Icon>,
};

const DEFAULT_ICON = style => <Icon style={style}>apps</Icon>;

export default ({ mimeType, style }) => {
  if (TYPE_RENDERER[mimeType]) {
    return TYPE_RENDERER[mimeType](style);
  }
  return DEFAULT_ICON(style);
};
