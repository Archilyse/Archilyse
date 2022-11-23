import domtoimage from 'dom-to-image';

const DOWNLOAD_HEIGHT = 1080;
const DOWNLOAD_WIDTH = 1920;

const defaultStyle = {
  backgroundColor: 'white',
  display: 'flex',
  justifyContent: 'space-around',
  alignItems: 'center',
};

const METHOD_BY_FILE_EXT = {
  jpeg: 'toJpeg',
  png: 'toPng',
};

// @TODO: If the user use a low resolution and the dom element is rendered different the result won't be consistent despite fixed height/width
export default async ({
  filename = 'image',
  id = '',
  ext = 'jpeg',
  height = DOWNLOAD_HEIGHT,
  width = DOWNLOAD_WIDTH,
  style = defaultStyle,
}) => {
  const method = METHOD_BY_FILE_EXT[ext];

  const dataUrl = await domtoimage[method](document.getElementById(id), { height, width, style });

  const link = document.createElement('a');
  link.download = `${filename}.${ext}`;
  link.href = dataUrl;
  link.click();
};
