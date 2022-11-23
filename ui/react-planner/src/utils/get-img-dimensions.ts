export default async (imgBlob: Blob): Promise<{ width: number; height: number; originalImgElem: HTMLImageElement }> => {
  return new Promise((resolve, reject) => {
    const imgUrl = URL.createObjectURL(imgBlob);
    const img = document.createElement('img');
    img.src = imgUrl;
    img.onload = async () => {
      return resolve({
        width: img.width,
        height: img.height,
        originalImgElem: img,
      });
    };
    img.onerror = error => reject(error);
  });
};
