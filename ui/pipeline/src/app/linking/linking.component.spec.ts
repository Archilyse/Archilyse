import { async, ComponentFixture, fakeAsync, flush, TestBed, tick } from '@angular/core/testing';

import { DebugElement } from '@angular/core';
import { By } from '@angular/platform-browser';
import { app_declarations } from '../app.declarations';
import { app_imports } from '../app.imports';
import { ActivatedRoute } from '@angular/router';
import { BrowserDynamicTestingModule } from '@angular/platform-browser-dynamic/testing';
import { TestingHelpers } from '../_shared-libraries/TestingHelpers';
import { LinkingComponent } from './linking.component';
import { HelpDialogLinkingComponent } from './help-linking/help-linking.component';
import { ApiService } from '../_services/api.service';
import { MockApiService } from '../_services/api.service.mock';
import { FloorplanLinkingService } from '../_services/floorplan/floorplan.linking.service';
import { ImgService } from '../_services/img.service';
import { MockImgService } from '../_services/img.service.mock';
import { MatSnackBar } from '@angular/material/snack-bar';
import * as validations from '../_shared-libraries/Validations';

describe('Linking component', () => {
  let copyright: DebugElement;
  let cardTitle: DebugElement;
  let comp: LinkingComponent;
  let fixture: ComponentFixture<LinkingComponent>;
  let apiService: ApiService;
  let snackBar: MatSnackBar;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [...app_declarations],
      imports: [...app_imports],
      providers: [
        LinkingComponent,
        FloorplanLinkingService,
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
        set: { entryComponents: [HelpDialogLinkingComponent] },
      })
      .compileComponents();
  }));

  beforeEach(async end => {
    apiService = TestBed.inject(ApiService);
    snackBar = TestBed.inject(MatSnackBar);
    fixture = TestBed.createComponent(LinkingComponent);
    comp = fixture.componentInstance;
    comp.plan_id = '1';
    await comp.loadData();

    cardTitle = fixture.debugElement.query(By.css('.card-title'));
    copyright = fixture.debugElement.query(By.css('.copyright'));
    end();
  });

  afterEach(() => {
    document.body.removeChild(fixture.debugElement.nativeElement);
    const helpElement = document.querySelector('.cdk-overlay-container');
    if (helpElement) {
      document.body.removeChild(helpElement);
    }
  });

  it('should create component', () => expect(comp).toBeDefined());

  it('should display the linking help', end => {
    TestingHelpers.testHelpButtonWithDialog(expect, fixture, end);
  });

  it('should properly display and error after an exception', () => {
    TestingHelpers.testDisplayErrorInComponent(expect, comp, fixture);
  });

  it('should have copyright list', () => {
    TestingHelpers.checkArchilyseFooter(expect, copyright, fixture);
  });

  it('trims the client id string on save', fakeAsync(() => {
    fixture.detectChanges();

    const updateUnitsSpy = spyOn(apiService, 'updateUnits').and.returnValue(Promise.resolve(true));

    const completeLinkingSpy = spyOn(apiService, 'completeLinking');
    comp.units = {
      floor_id: [
        { id: 1, client_id: ' untrimmed_id ', unit_usage: 'RESIDENTIAL' },
        { id: 99, client_id: 'noice', unit_usage: 'COMMERCIAL' },
      ],
    };

    comp.onSave();

    tick();
    flush();

    const expectedUnits = [
      { id: 1, client_id: 'untrimmed_id', unit_usage: 'RESIDENTIAL' },
      { id: 99, client_id: 'noice', unit_usage: 'COMMERCIAL' },
    ];

    expect(updateUnitsSpy).toHaveBeenCalledWith(comp.plan_id, expectedUnits);
    expect(completeLinkingSpy).toHaveBeenCalled();
  }));

  it('sets empty client id string upon saving if not existent', fakeAsync(() => {
    fixture.detectChanges();

    const updateUnitsSpy = spyOn(apiService, 'updateUnits').and.returnValue(Promise.resolve(true));

    const completeLinkingSpy = spyOn(apiService, 'completeLinking');
    comp.units = {
      floor_id: [
        { id: 2, unit_usage: 'RESIDENTIAL' },
        { id: 765, klient_id: 'noice', unit_usage: 'COMMERCIAL' },
      ],
    };

    comp.onSave();

    tick();
    flush();

    const expectedUnits = [
      { id: 2, client_id: '', unit_usage: 'RESIDENTIAL' },
      { id: 765, client_id: '', unit_usage: 'COMMERCIAL' },
    ];

    expect(updateUnitsSpy).toHaveBeenCalledWith(comp.plan_id, expectedUnits);
    expect(completeLinkingSpy).toHaveBeenCalled();
  }));

  it('should display error message if api calls return 4xx', fakeAsync(() => {
    fixture.detectChanges();

    const errorMsg = 'api call failed';
    spyOn(apiService, 'updateUnits').and.throwError(errorMsg);
    const completeLinkingSpy = spyOn(apiService, 'completeLinking');
    const snackBarSpy = spyOn(snackBar, 'open');
    const linkingErrorSpy = spyOn(comp, 'parseError');

    comp.onSave();

    tick();
    flush();

    expect(linkingErrorSpy).toHaveBeenCalledWith(
      Error(errorMsg),
      'Error linking the units, check the console (F12) and report the problem.'
    );
    expect(snackBarSpy).not.toHaveBeenCalled();
    expect(completeLinkingSpy).not.toHaveBeenCalled();
  }));

  it('should not update units if shouldSave evals to "false"', fakeAsync(() => {
    fixture.detectChanges();

    const shouldSaveSpy = spyOn(validations, 'shouldSave').and.returnValue(Promise.resolve(true));
    const updateUnitsSpy = spyOn(apiService, 'updateUnits').and.returnValue(Promise.resolve(true));
    const completeLinkingSpy = spyOn(apiService, 'completeLinking');

    comp.onSave();

    tick();
    flush();

    expect(updateUnitsSpy).toHaveBeenCalled();
    expect(shouldSaveSpy).toHaveBeenCalledWith(apiService, comp.plan_id);
    expect(completeLinkingSpy).toHaveBeenCalled();
  }));
});
