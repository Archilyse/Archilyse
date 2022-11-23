import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { UnitQaComponent } from './unit-qa.component';
import { app_declarations } from '../../app.declarations';
import { app_imports } from '../../app.imports';
import { ApiService } from '../../_services/api.service';
import { MockApiService } from '../../_services/api.service.mock';

const exampleUnit = {
  client_id: 1,
  plan_id: 1,
  area_ids: [],
  m2: null,
  rooms: null,
};

describe('Unit quality component', () => {
  let comp: UnitQaComponent;
  let fixture: ComponentFixture<UnitQaComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [...app_declarations],
      imports: [...app_imports],
      providers: [UnitQaComponent, { provide: ApiService, useClass: MockApiService }],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(UnitQaComponent);
    comp = fixture.componentInstance;
  });
  afterEach(() => {
    document.body.removeChild(fixture.debugElement.nativeElement);
  });

  it('should create component', () => expect(comp).toBeDefined());

  it('should generate no warning strings', end => {
    comp.unit = exampleUnit;
    comp.unit.client_id = `Doesn't exist`;
    comp.site_id = 1;
    fixture.detectChanges();
    fixture.whenStable().then(() => {
      expect(comp.warningsStr).toBe('');
      end();
    });
  });

  it('should generate a warning string', end => {
    comp.unit = exampleUnit;
    comp.unit.client_id = '2103180.01.01.0001';
    comp.unit.m2 = 10000;
    comp.unit.rooms = null;
    comp.site_id = 1;
    fixture.detectChanges();
    fixture.whenStable().then(() => {
      expect(comp.warningsStr).toBe(
        `Net area doesn't match: Current value 10000m<sup>2</sup> expected 53m<sup>2</sup>`
      );
      end();
    });
  });

  it('should generate 2 warning strings', end => {
    comp.unit = exampleUnit;
    comp.unit.client_id = '2103180.01.01.0001';
    comp.unit.m2 = 10000;
    comp.unit.rooms = 10;
    comp.site_id = 1;
    fixture.detectChanges();
    fixture.whenStable().then(() => {
      expect(comp.warningsStr).toBe(
        `Net area doesn't match: Current value 10000m<sup>2</sup> expected 53m<sup>2</sup><br/>Number of rooms doesn't match: Current value 10 expected 2`
      );
      end();
    });
  });
});
