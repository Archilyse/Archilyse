import { OverlayRef } from '@angular/cdk/overlay';

/**
 * Generic class for overlays
 */
export class GenericOverlayRef {
  constructor(private overlayRef: OverlayRef) {}

  close(): void {
    this.overlayRef.dispose();
  }
}
