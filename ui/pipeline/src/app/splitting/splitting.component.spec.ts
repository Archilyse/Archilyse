import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { DebugElement } from '@angular/core';
import { By } from '@angular/platform-browser';
import { app_declarations } from '../app.declarations';
import { app_imports } from '../app.imports';
import { ActivatedRoute } from '@angular/router';
import { BrowserDynamicTestingModule } from '@angular/platform-browser-dynamic/testing';
import { TestingHelpers } from '../_shared-libraries/TestingHelpers';
import { SplittingComponent } from './splitting.component';
import { HelpDialogSplittingComponent } from './help-splitting/help-splitting.component';
import { ApiService } from '../_services/api.service';
import { MockApiService } from '../_services/api.service.mock';
import { GoogleAnalyticsService } from 'ngx-google-analytics';
import { MockGoogleAnalyticsService } from '../_services/google-analytics.service.mock';
import { FloorplanSplittingService } from '../_services/floorplan/floorplan.splitting.service';
import { ImgService } from '../_services/img.service';
import { MockImgService } from '../_services/img.service.mock';
import { EditorConstants } from '../_shared-libraries/EditorConstants';

function assertWellCreatedApartment(newApartment, newId) {
  expect(newApartment.id).toBe(newId);
  expect(newApartment.areasId.length).toBe(0);
  expect(newApartment.rooms).toBe(0);
  expect(Object.keys(newApartment.m2report).length).toBe(0);
  expect(EditorConstants.COLORS.includes(newApartment.color)).toBeTrue();
}

describe('Splitting component', () => {
  let copyright: DebugElement;
  let cardTitle: DebugElement;
  let comp: SplittingComponent;
  let fixture: ComponentFixture<SplittingComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [...app_declarations],
      imports: [...app_imports],
      providers: [
        SplittingComponent,
        FloorplanSplittingService,
        { provide: ApiService, useClass: MockApiService },
        { provide: ImgService, useClass: MockImgService },
        {
          provide: GoogleAnalyticsService,
          useClass: MockGoogleAnalyticsService,
        },
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
        set: { entryComponents: [HelpDialogSplittingComponent] },
      })
      .compileComponents();
  }));

  beforeEach(async end => {
    fixture = TestBed.createComponent(SplittingComponent);
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

  it('should display the scaling help', end => {
    TestingHelpers.testHelpButtonWithDialog(expect, fixture, end);
  });

  it('should properly display and error after an exception', () => {
    TestingHelpers.testDisplayErrorInComponent(expect, comp, fixture);
  });

  it('should create a new apartment with a fixed id', () => {
    const newId = 100;
    const newApartment = comp.newApartment(newId);
    assertWellCreatedApartment(newApartment, newId);
  });
  it('should create a new apartment with a new id', () => {
    const newId = null;
    const newApartment = comp.newApartment(newId);
    const expectedId = 2;
    assertWellCreatedApartment(newApartment, expectedId);
  });
  it('should have copyright list', () => {
    TestingHelpers.checkArchilyseFooter(expect, copyright, fixture);
  });

  it('should reload model structure when errors are provided', () => {
    const error = 'Normal error';
    const isSpacial = comp.parseBrooksError(error);
    expect(isSpacial).toBeFalse();

    const errorBrooks = {
      error: {
        errors: [1, 2],
      },
    };
    const isSpacial2 = comp.parseBrooksError(errorBrooks);
    expect(isSpacial2).toBeTrue();
  });

  it('should determine to increase the not defined', () => {
    const nextChangePublic = {
      old: 1,
      new: -1,
    };
    const nextChangeNull = {
      old: 1,
      new: null,
    };
    const nextChangeValue = {
      old: 1,
      new: 1,
    };
    expect(comp.shouldIncreaseNotDefined(nextChangePublic)).toBeFalse();
    expect(comp.shouldIncreaseNotDefined(nextChangeNull)).toBeFalse();
    expect(comp.shouldIncreaseNotDefined(nextChangeValue)).toBeTrue();
  });

  it('should parse the basic feature calculation', () => {
    const result = {};

    result['number-of-rooms'] = 1;
    result['area-sia416-ANF'] = 1.1;
    result['area-sia416-FF'] = 1.2;
    result['area-sia416-HNF'] = 1.3;
    result['area-sia416-NNF'] = 1.4;
    result['area-sia416-VF'] = 1.5;

    // It doesn't fail with null apartment
    const apartment = null;
    comp.updateM2report(apartment, result);
    expect(apartment).toBeNull();

    const apartmentOk = {};
    comp.updateM2report(apartmentOk, result);
    expect(apartmentOk['rooms']).toBe(1);
    expect(apartmentOk['ANF']).toBe(1.1);
    expect(apartmentOk['FF']).toBe(1.2);
    expect(apartmentOk['HNF']).toBe(1.3);
    expect(apartmentOk['NNF']).toBe(1.4);
    expect(apartmentOk['VF']).toBe(1.5);
  });

  it('should remove an area from the area array id', () => {
    const areaIdsArray = ['2', '1'];
    const areaIdNotExistent = '3';
    comp.removeAreaFromArray(areaIdsArray, areaIdNotExistent);
    expect(areaIdsArray.length).toBe(2);

    const areaId = '1';
    comp.removeAreaFromArray(areaIdsArray, areaId);
    expect(areaIdsArray.length).toBe(1);
  });
});
