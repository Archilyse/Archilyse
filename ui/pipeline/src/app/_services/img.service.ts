import { Injectable } from '@angular/core';
import { Texture } from 'three-full/builds/Three.es';

@Injectable({
  providedIn: 'root',
})
export class ImgService {
  constructor() {}

  /**
   * Load the picture specified in the plan object by the attribute 'image_gcs_link' (if any)
   * Fills the backgroundImg field in the component and also:
   * backgroundImgWidth with the image with * brooks scale
   * backgroundImgHeight with the image height * brooks scale
   * @param component
   * @param planData
   * @param brooks
   */
  async loadBackgroundImg(component, planData, apiService) {
    if (!planData) {
      return;
    }
    try {
      const response = await apiService.getPlanBackgroundImage(planData.id);
      const imageTransformation = await apiService.getPlanBackgroundImageTransformation(planData.id);

      component.backgroundImgScale = imageTransformation.scale;
      component.backgroundImgRotation = imageTransformation.rotation;
      component.backgroundImgShiftX = imageTransformation.shift_x;
      component.backgroundImgShiftY = imageTransformation.shift_y;
      const image = new Image();
      const blobUrl = URL.createObjectURL(response);
      image.src = blobUrl;

      return new Promise((resolve, reject) => {
        image.onload = () => {
          const texture = new Texture(image);
          if (texture) {
            component.backgroundImg = texture;
            component.backgroundImgWidth = texture.image.width;
            component.backgroundImgHeight = texture.image.height;
          }

          texture.needsUpdate = true;
          resolve(texture);
        };
        image.onerror = error => {
          reject(error);
        };
      });
    } catch (error) {
      console.log('Error loading background image', error);
      throw error;
    }
  }
}
