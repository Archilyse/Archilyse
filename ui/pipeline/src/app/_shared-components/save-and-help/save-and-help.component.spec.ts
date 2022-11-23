import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { DebugElement } from '@angular/core';
import { By } from '@angular/platform-browser';
import { app_declarations } from '../../app.declarations';
import { app_imports } from '../../app.imports';
import { SaveAndHelpComponent } from './save-and-help.component';

describe('Save and help component', () => {
  let saveButton: DebugElement;
  let validateButton: DebugElement;
  let helpButton: DebugElement;

  let comp: SaveAndHelpComponent;
  let fixture: ComponentFixture<SaveAndHelpComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [...app_declarations],
      imports: [...app_imports],
      providers: [SaveAndHelpComponent],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SaveAndHelpComponent);
    comp = fixture.componentInstance;
  });
  afterEach(() => {
    document.body.removeChild(fixture.debugElement.nativeElement);
  });

  it('should create component', () => expect(comp).toBeDefined());
  it('should have save, validate and help buttons', () => {
    const saveText = 'Save Button';
    const validateText = 'Validate Button';

    comp.saving = false;
    comp.saveText = saveText;
    comp.extraText = validateText;
    comp.disabled = false;

    fixture.detectChanges();

    saveButton = fixture.debugElement.query(By.css('#save_button'));
    validateButton = fixture.debugElement.query(By.css('#validate_button'));
    helpButton = fixture.debugElement.query(By.css('#help_button'));

    expect(saveButton).toBeDefined();
    expect(saveButton.nativeElement.innerText).toBe(saveText);

    expect(validateButton).toBeDefined();
    expect(validateButton.nativeElement.innerText).toBe(validateText);

    expect(helpButton).toBeDefined();
    expect(helpButton.nativeElement.innerText).toBe('Help');
  });

  it('should ONLY have save, NOT validate and help buttons', () => {
    comp.saving = false;
    comp.extraText = null;
    comp.disabled = false;

    fixture.detectChanges();

    const saveButton = fixture.debugElement.query(By.css('#save_button'));
    const validateButton = fixture.debugElement.query(By.css('#validate_button'));
    const helpButton = fixture.debugElement.query(By.css('#help_button'));

    expect(saveButton).toBeDefined();
    expect(validateButton).toBeNull();
    expect(helpButton).toBeDefined();
    expect(helpButton.nativeElement.innerText).toBe('Help');
  });
});
