import { Component } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'help-dialog-quality-component',
  templateUrl: './help-quality.html',
  styleUrls: ['./help-quality.component.scss'],
})
export class HelpDialogQualityComponent {
  constructor(public dialogRef: MatDialogRef<HelpDialogQualityComponent>) {}
}
