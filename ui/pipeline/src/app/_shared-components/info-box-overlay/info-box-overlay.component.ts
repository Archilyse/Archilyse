import { Component, Inject } from '@angular/core';
import { GenericOverlayRef } from './generic-overlay-ref';
import { INFO_BOX_OVERLAY_DATA } from './info-box-overlay.tokens';

/**
 * Information overlay layout
 */
@Component({
  selector: 'info-box-overlay',
  template: `
    <div class="card">
      <h4 [innerHTML]="data.title"></h4>
      <img *ngIf="data.image" src="assets/images/info/{{ data.image }}.png" alt="" />
      <p [innerHTML]="data.body"></p>
    </div>
  `,
  styleUrls: ['./info-box-overlay.component.scss'],
})
export class InfoBoxOverlayComponent {
  constructor(public dialogRef: GenericOverlayRef, @Inject(INFO_BOX_OVERLAY_DATA) public data: any) {}
}
