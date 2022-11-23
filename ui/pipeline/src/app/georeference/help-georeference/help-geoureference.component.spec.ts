import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { app_declarations } from '../../app.declarations';
import { app_imports } from '../../app.imports';
import { MatDialogRef } from '@angular/material/dialog';
import { HelpDialogGeoreferenceComponent } from './help-georeference.component';

describe('Help georeference component', () => {
  let comp: HelpDialogGeoreferenceComponent;
  let fixture: ComponentFixture<HelpDialogGeoreferenceComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [...app_declarations],
      imports: [...app_imports],
      providers: [HelpDialogGeoreferenceComponent, { provide: MatDialogRef, useValue: {} }],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(HelpDialogGeoreferenceComponent);
    comp = fixture.componentInstance;
  });

  afterEach(() => {
    try {
      document.body.removeChild(fixture.debugElement.nativeElement);
      const helpElement = document.querySelector('.cdk-overlay-container');
      if (helpElement) {
        document.body.removeChild(helpElement);
      }
    } catch (e) {}
  });

  it('should create component', () => expect(comp).toBeDefined());
});
