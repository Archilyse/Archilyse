import { Component } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'help-dialog-classification-component',
  templateUrl: './help-classification.html',
  styleUrls: ['./help-classification.component.scss'],
})
export class HelpDialogClassificationComponent {
  constructor(public dialogRef: MatDialogRef<HelpDialogClassificationComponent>) {}
}
