import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-save-and-help',
  templateUrl: './save-and-help.component.html',
  styleUrls: ['./save-and-help.component.scss'],
})
export class SaveAndHelpComponent {
  @Input() saving;

  @Input() saveText = 'Save';
  @Input() savingText = null;
  @Output() save = new EventEmitter();

  @Input() extraText = null;
  @Input() extraTextToolTip = null;
  @Input() extraTextNextColumn = false;
  @Output() extraFunction = new EventEmitter();

  @Input() disabled = false;
  @Input() validateDisabled = false;

  @Output() openDialog = new EventEmitter();

  constructor() {}

  save_parent() {
    this.save.emit(null);
  }
  extra_parent() {
    this.extraFunction.emit(null);
  }
  openDialog_parent() {
    this.openDialog.emit(null);
  }
}
