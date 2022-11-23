import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { app_declarations } from '../../app.declarations';
import { app_imports } from '../../app.imports';
import { MatDialogRef } from '@angular/material/dialog';
import { HelpDialogClassificationComponent } from './help-classification.component';
import { ApiService } from '../../_services/api.service';
import { MockApiService } from '../../_services/api.service.mock';

describe('Help classification component', () => {
  let comp: HelpDialogClassificationComponent;
  let fixture: ComponentFixture<HelpDialogClassificationComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [...app_declarations],
      imports: [...app_imports],
      providers: [
        HelpDialogClassificationComponent,
        { provide: ApiService, useClass: MockApiService },
        { provide: MatDialogRef, useValue: {} },
      ],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(HelpDialogClassificationComponent);
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
