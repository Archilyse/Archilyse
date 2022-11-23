import { Component } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'help-dialog-georeference-component',
  templateUrl: './help-georeference.html',
  styleUrls: ['./help-georeference.component.scss'],
})
export class HelpDialogGeoreferenceComponent {
  constructor(public dialogRef: MatDialogRef<HelpDialogGeoreferenceComponent>) {}
}
