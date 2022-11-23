import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { DebugElement } from '@angular/core';
import { By } from '@angular/platform-browser';
import { ClassificationComponent } from './classification.component';
import { app_declarations } from '../app.declarations';
import { app_imports } from '../app.imports';
import { ActivatedRoute } from '@angular/router';
import { HelpDialogClassificationComponent } from './help-classification/help-classification.component';
import { BrowserDynamicTestingModule } from '@angular/platform-browser-dynamic/testing';
import { TestingHelpers } from '../_shared-libraries/TestingHelpers';
import { OverlayService } from '../_services/overlay.service';
import { ApiService } from '../_services/api.service';
import { MockApiService } from '../_services/api.service.mock';
import { FloorplanClassificationService } from '../_services/floorplan/floorplan.classification.service';
import { ImgService } from '../_services/img.service';
import { MockImgService } from '../_services/img.service.mock';

describe('Classification component', () => {
  let copyright: DebugElement;
  let comp: ClassificationComponent;
  let fixture: ComponentFixture<ClassificationComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [...app_declarations],
      imports: [...app_imports],
      providers: [
        OverlayService,
        ClassificationComponent,
        FloorplanClassificationService,
        { provide: ApiService, useClass: MockApiService },
        { provide: ImgService, useClass: MockImgService },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              params: {
                plan_id: '1',
              },
            },
          },
        },
      ],
    })
      .overrideModule(BrowserDynamicTestingModule, {
        set: { entryComponents: [HelpDialogClassificationComponent] },
      })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ClassificationComponent);
    comp = fixture.componentInstance;
    comp.site_id = '1';
    comp.planData = {
      id: 1,
      site_id: 1,
    };
    comp.loadData();
    copyright = fixture.debugElement.query(By.css('.copyright'));
  });
  afterEach(() => {
    document.body.removeChild(fixture.debugElement.nativeElement);
  });

  it('should create component', () => expect(comp).toBeDefined());

  it('should display the classification help', end => {
    TestingHelpers.testHelpButtonWithDialog(expect, fixture, end);
  });

  it('should have the save button blocked, make a change and the save button disable', () => {
    // This functionality is repeated also in classification and splitting
    TestingHelpers.testSaveButtonOnlyWhenModified(expect, comp, fixture);
  });

  it('should properly display and error after an exception', () => {
    TestingHelpers.testDisplayErrorInComponent(expect, comp, fixture);
  });

  it('should have copyright list', () => {
    TestingHelpers.checkArchilyseFooter(expect, copyright, fixture);
  });
});
