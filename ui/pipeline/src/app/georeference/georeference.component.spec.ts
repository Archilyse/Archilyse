import { async, ComponentFixture, fakeAsync, TestBed, tick } from '@angular/core/testing';
import { app_declarations } from '../app.declarations';
import { app_imports } from '../app.imports';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../_services/api.service';
import { GoogleAnalyticsService } from 'ngx-google-analytics';
import { MockGoogleAnalyticsService } from '../_services/google-analytics.service.mock';
import { GeoreferenceComponent } from './georeference.component';
import { MockApiService } from '../_services/api.service.mock';
import { MockEventStreamApiService } from '../_services/eventstreamapi.service.mock';
import { EventStreamApiService } from '../_services/eventstreamapi.service';
import { Observable } from 'rxjs/internal/Observable';

describe('verify fetched data from api by georeference component', () => {
  let component: GeoreferenceComponent;
  let fixture: ComponentFixture<GeoreferenceComponent>;
  let apiService: ApiService;
  let eventstreamService: EventStreamApiService;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [...app_declarations],
      imports: [...app_imports],
      providers: [
        GeoreferenceComponent,
        { provide: ApiService, useClass: MockApiService },
        { provide: EventStreamApiService, useClass: MockEventStreamApiService },
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
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GeoreferenceComponent);
    component = fixture.componentInstance;
    apiService = TestBed.inject(ApiService);
    eventstreamService = TestBed.inject(EventStreamApiService);
  });

  it('creates component', () => expect(component).toBeDefined());

  it('sets parameters for scaled, not georeferenced plan', fakeAsync(() => {
    /**
     * Given a scaled, not georeferenced plan (no georef_x, georef_y)
     * When loading a plan in the Georeference Component
     * Then the map is set up with non-georeferenced plan parameters
     */
    fixture.detectChanges();
    spyOn(apiService, 'getPlanData').and.returnValue(Promise.resolve({ site_id: '1', georef_scale: 0.001 }));
    const buildingSurroundingsSpy = spyOn(apiService, 'getSurroundingBuildingsFootprints').and.returnValue(
      Promise.resolve(true)
    );
    const otherPlansSpy = spyOn(eventstreamService, 'getGeoreferencedPlansUnderSameSite').and.returnValue(
      new Observable()
    );
    const planFootprintSpy = spyOn(apiService, 'getFootprintById').and.returnValue(Promise.resolve(true));
    const setUpMapSpy = spyOn(component, 'setUpMap');

    component.loadData();

    tick();

    expect(buildingSurroundingsSpy).toHaveBeenCalled();
    expect(otherPlansSpy).toHaveBeenCalled();
    expect(planFootprintSpy).toHaveBeenCalled();
    expect(setUpMapSpy).toHaveBeenCalled();
  }));

  it('sets parameters for scaled, georeferenced plan', fakeAsync(() => {
    /**
     * Given a scaled, georeferenced plan
     * When loading a plan in the Georeference Component
     * Then the map is set up with georeferenced plan parameters
     */
    fixture.detectChanges();
    spyOn(apiService, 'getPlanData').and.returnValue(
      Promise.resolve({ site_id: '1', georef_scale: 0.001, georef_x: 1, georef_y: 1 })
    );

    const buildingSurroundingsSpy = spyOn(apiService, 'getSurroundingBuildingsFootprints').and.returnValue(
      Promise.resolve(true)
    );
    const otherPlansSpy = spyOn(eventstreamService, 'getGeoreferencedPlansUnderSameSite').and.returnValue(
      new Observable()
    );
    const planFootprintSpy = spyOn(apiService, 'getFootprintById').and.returnValue(Promise.resolve(true));
    const setUpMapSpy = spyOn(component, 'setUpMap');

    component.loadData();

    tick();

    expect(buildingSurroundingsSpy).toHaveBeenCalled();
    expect(otherPlansSpy).toHaveBeenCalled();
    expect(planFootprintSpy).toHaveBeenCalled();
    expect(setUpMapSpy).toHaveBeenCalled();
  }));

  it('subscribes to the event stream API once the OpenLayers map has been initialized', fakeAsync(() => {
    /**
     * Given a request to get the plan footprint
     * When the response is successful
     * Then the georef component subscribes to the API events to load other plan footprints.
     */
    const expectedResult = { type: 'Polygon', coordinates: [[]] };
    spyOn(apiService, 'getPlanData').and.returnValue(
      Promise.resolve({ site_id: '1', georef_scale: 0.001, georef_x: 1, georef_y: 1 })
    );
    const buildingSurroundingsSpy = spyOn(apiService, 'getSurroundingBuildingsFootprints').and.returnValue(
      Promise.resolve(true)
    );
    const otherPlansSpy = spyOn(eventstreamService, 'getGeoreferencedPlansUnderSameSite').and.returnValue(
      new Observable()
    );
    spyOn(apiService, 'getFootprintById').and.returnValue(Promise.resolve(expectedResult));
    const setUpMapSpy = spyOn(component, 'setUpMap').and.callFake(() => {
      component.globalSource = { forEachFeature: jasmine.createSpy() };
    });

    component.loadData();

    tick();

    expect(setUpMapSpy).toHaveBeenCalled();
    expect(component.footprintData).toEqual(expectedResult);
    expect(component.globalSource).toBeTruthy();
    expect(otherPlansSpy).toHaveBeenCalled();
  }));
});
