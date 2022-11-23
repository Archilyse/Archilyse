const MAXIMUM_IMAGE_WIDTH = 4000;

export const getDownScaledImage = async ({ originalImgElem, imgBlob }): Promise<Blob> => {
  const shouldDownScaleImage = originalImgElem.width > MAXIMUM_IMAGE_WIDTH;
  let image = imgBlob;
  if (shouldDownScaleImage) {
    const imgUrl = originalImgElem.src;
    image = await downscaleImage({ imgUrl, newWidth: MAXIMUM_IMAGE_WIDTH, imageType: imgBlob.type });
  }
  return image;
};

// https://stackoverflow.com/a/39735336
async function downscaleImage({ imgUrl, newWidth, imageType = 'image/jpeg' }) {
  // Create a temporary image so that we can compute the height of the downscaled image.
  const image = new Image();
  image.src = imgUrl;
  const oldWidth = image.width;
  const oldHeight = image.height;
  const newHeight = Math.floor((oldHeight / oldWidth) * newWidth);

  // Create a temporary canvas to draw the downscaled image on.
  const canvas = document.createElement('canvas');
  canvas.width = newWidth;
  canvas.height = newHeight;

  // Draw the downscaled image on the canvas and return the new data URL.
  const ctx = canvas.getContext('2d');
  ctx.drawImage(image, 0, 0, newWidth, newHeight);
  const blobDataImg = await new Promise(resolve => canvas.toBlob(resolve, imageType));
  return blobDataImg;
}
