import { Injectable, Injector, ComponentRef } from '@angular/core';
import { Overlay, OverlayConfig, OverlayRef } from '@angular/cdk/overlay';
import { ComponentPortal, PortalInjector } from '@angular/cdk/portal';
import { GenericOverlayRef } from '../_shared-components/info-box-overlay/generic-overlay-ref';
import { InfoBoxOverlayComponent } from '../_shared-components/info-box-overlay/info-box-overlay.component';
import { INFO_BOX_OVERLAY_DATA } from '../_shared-components/info-box-overlay/info-box-overlay.tokens';

/**
 * Configuration options of the Info box
 */
interface InfoBoxDialogConfig {
  panelClass?: string;
  hasBackdrop?: boolean;
  backdropClass?: string;
  data?: any;
  // image?: Image;
}

/**
 * Default option of the Info box
 */
const DEFAULT_CONFIG: InfoBoxDialogConfig = {
  hasBackdrop: true,
  backdropClass: 'dark-backdrop',
  panelClass: 'info-box-dialog-panel',
};

/**
 * The OverlayService allow to display messages for the user over the content
 */
@Injectable()
export class OverlayService {
  /** Constructor */
  constructor(private injector: Injector, private overlay: Overlay) {}

  open(config: InfoBoxDialogConfig = {}) {
    // Override default configuration
    const dialogConfig = { ...DEFAULT_CONFIG, ...config };

    // Returns an OverlayRef which is a PortalHost
    const overlayRef = this.createOverlay(dialogConfig);

    // Instantiate remote control
    const dialogRef = new GenericOverlayRef(overlayRef);

    this.attachDialogContainer(overlayRef, dialogConfig, dialogRef);

    overlayRef.backdropClick().subscribe(_ => dialogRef.close());

    return dialogRef;
  }

  private createOverlay(config: InfoBoxDialogConfig) {
    const overlayConfig = this.getOverlayConfig(config);
    return this.overlay.create(overlayConfig);
  }

  private attachDialogContainer(overlayRef: OverlayRef, config: InfoBoxDialogConfig, dialogRef: GenericOverlayRef) {
    const injector = this.createInjector(config, dialogRef);

    const containerPortal = new ComponentPortal(InfoBoxOverlayComponent, null, injector);
    const containerRef: ComponentRef<InfoBoxOverlayComponent> = overlayRef.attach(containerPortal);

    return containerRef.instance;
  }

  private createInjector(config: InfoBoxDialogConfig, dialogRef: GenericOverlayRef): PortalInjector {
    const injectionTokens = new WeakMap();

    injectionTokens.set(GenericOverlayRef, dialogRef);
    injectionTokens.set(INFO_BOX_OVERLAY_DATA, config.data);

    return new PortalInjector(this.injector, injectionTokens);
  }

  private getOverlayConfig(config: InfoBoxDialogConfig): OverlayConfig {
    const positionStrategy = this.overlay.position().global().centerHorizontally().centerVertically();

    /**
     * Overlay config
     */
    return new OverlayConfig({
      positionStrategy,
      hasBackdrop: config.hasBackdrop,
      backdropClass: config.backdropClass,
      panelClass: config.panelClass,
      scrollStrategy: this.overlay.scrollStrategies.block(),
    });
  }
}
