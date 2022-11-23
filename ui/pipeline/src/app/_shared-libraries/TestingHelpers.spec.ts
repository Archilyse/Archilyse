import { TestingHelpers } from './TestingHelpers';
import { Component, HostListener } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { app_declarations } from '../app.declarations';
import { app_imports } from '../app.imports';
import { By } from '@angular/platform-browser';
import { BaseComponent } from '../base.component';

/**
 * This component it's a mock to test the validation functions
 */
@Component({
  selector: 'app-fake-component',
  template: `
    <div>Fake component</div>
    <div *ngIf="error" id="errorMessage" class="errorMessage">{{ error }}</div>
    <app-save-and-help
      [saving]="saving"
      [disabled]="saveDisabled"
      [saveText]="saveText"
      (save)="onSave()"
      (openDialog)="openDialog()"
    ></app-save-and-help>
    <app-footer></app-footer>
  `,
})
export class FakeComponent extends BaseComponent {
  keydownX = false;
  keyupX = false;

  onSave() {}
  openDialog() {}

  @HostListener('document:keydown', ['$event'])
  handleKeyDown(e) {
    // Key x
    if (e.which === 'x') {
      this.keydownX = true;
    }
  }
  @HostListener('document:keyup', ['$event'])
  handleKeyUp(e) {
    // Key x
    if (e.which === 'x') {
      this.keyupX = true;
    }
  }
}

describe('Testing Helpers.ts library', () => {
  let comp: FakeComponent;
  let fixture: ComponentFixture<FakeComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [...app_declarations, FakeComponent],
      imports: [...app_imports],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FakeComponent);
    comp = fixture.componentInstance;
  });
  afterEach(() => {
    document.body.removeChild(fixture.debugElement.nativeElement);
  });

  it('should throw the keyDown event and register it in a component', () => {
    const keyPressed = 'x';
    TestingHelpers.keyDown(fixture, keyPressed);
    expect(comp.keydownX).toBe(true);
  });

  it('should throw the keyUp event and register it in a component', () => {
    const keyPressed = 'x';
    TestingHelpers.keyUp(fixture, keyPressed);
    expect(comp.keyupX).toBe(true);
  });
  it('should detect that theres a save button only available the something changed ', () => {
    TestingHelpers.testSaveButtonOnlyWhenModified(expect, comp, fixture);
  });
  it('should properly display an error', () => {
    TestingHelpers.testDisplayErrorInComponent(expect, comp, fixture);
  });
  it('should detect that the component has a copyright', () => {
    const copyright = fixture.debugElement.query(By.css('.copyright'));
    TestingHelpers.checkArchilyseFooter(expect, copyright, fixture);
  });
});
