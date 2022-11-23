import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-map-mode',
  templateUrl: './map-mode.component.html',
  styleUrls: ['./map-mode.component.scss'],
})
export class MapModeComponent {
  @Output() changeMap = new EventEmitter();
  @Input() mapStyle;
  @Input() labelText;

  constructor() {}

  changeMapHandler(event) {
    this.changeMap.emit(event);
  }
}
