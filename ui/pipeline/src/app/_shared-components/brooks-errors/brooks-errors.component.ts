import { Component, OnInit, Input } from '@angular/core';
import { EditorService } from '../../_services/editor.service';

@Component({
  selector: 'app-brooks-errors',
  templateUrl: './brooks-errors.component.html',
  styleUrls: ['./brooks-errors.component.scss'],
})
export class BrooksErrorsComponent implements OnInit {
  @Input() model;

  constructor(public editorService: EditorService) {}

  ngOnInit(): void {}

  hoverError(errorIndex) {
    // We notify the editor the error that was selected
    this.editorService.highlightErrorFloorplan(errorIndex, this.model.errors[errorIndex]);
  }
}
