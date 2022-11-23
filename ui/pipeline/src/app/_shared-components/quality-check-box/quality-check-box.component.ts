import { Component, Input, OnInit } from '@angular/core';
import { ApiService } from '../../_services/api.service';
import { MatSnackBar } from '@angular/material/snack-bar';

const SAVE_NOTES = 'Save';
const SAVING_NOTES = 'Saving...';
const NOTES_SAVED = 'Saved';

@Component({
  selector: 'app-quality-check-box',
  templateUrl: './quality-check-box.component.html',
  styleUrls: ['./quality-check-box.component.scss'],
})
export class QualityCheckBoxComponent implements OnInit {
  @Input() site_id;
  @Input() always_open = false;

  saveNotesText = NOTES_SAVED;
  validation_notes;
  validation_notes_original;

  open = false;
  changed = false;

  constructor(public apiService: ApiService, public snackBar: MatSnackBar) {}

  ngOnInit(): void {
    this.getSiteData();
  }

  async getSiteData() {
    const site = await this.apiService.getSite(this.site_id);
    this.validation_notes_original = site.validation_notes ? site.validation_notes : '';
    this.validation_notes = this.validation_notes_original;
    this.changed = false;
  }

  toggle() {
    if (!this.always_open) {
      this.open = !this.open;
      this.restoreValue();
    }
  }

  restoreValue() {
    this.saveNotesText = NOTES_SAVED;
    this.validation_notes = this.validation_notes_original;
    this.changed = false;
  }

  onChangeNotes(event) {
    this.validation_notes = event;
    this.changed = this.validation_notes !== this.validation_notes_original;
    this.saveNotesText = this.changed ? SAVE_NOTES : NOTES_SAVED;
  }

  async onSaveNotes() {
    try {
      this.saveNotesText = SAVING_NOTES;
      await this.apiService.updateSite(this.site_id, {
        validation_notes: this.validation_notes,
      });
      this.saveNotesText = NOTES_SAVED;
      this.validation_notes_original = this.validation_notes;
      this.changed = false;
      this.snackBar.open('Quality notes saved', 'Okay', {});
    } catch (e) {
      this.saveNotesText = SAVE_NOTES;
      this.parseError(e);
    }
  }

  parseError(e) {
    this.snackBar.open('Error found while saving, check the console (F12)', 'Okay', {});
    console.error(e);
  }

  onKeyDown($event: KeyboardEvent) {
    $event.stopPropagation();
  }
}
