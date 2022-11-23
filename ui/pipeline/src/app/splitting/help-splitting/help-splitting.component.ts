import { Component } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'help-dialog-splitting-component',
  templateUrl: './help-splitting.html',
  styleUrls: ['./help-splitting.component.scss'],
})
export class HelpDialogSplittingComponent {
  constructor(public dialogRef: MatDialogRef<HelpDialogSplittingComponent>) {}
}
