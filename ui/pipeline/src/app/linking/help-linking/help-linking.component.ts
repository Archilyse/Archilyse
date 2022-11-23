import { Component } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'help-dialog-linking-component',
  templateUrl: './help-linking.html',
  styleUrls: ['./help-linking.component.scss'],
})
export class HelpDialogLinkingComponent {
  constructor(public dialogRef: MatDialogRef<HelpDialogLinkingComponent>) {}
}
