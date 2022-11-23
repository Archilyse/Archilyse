import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { GeoreferenceComponent } from './georeference.component';
import { app_declarations } from '../app.declarations';
import { app_imports } from '../app.imports';
import { ActivatedRoute } from '@angular/router';
import { EventStreamApiService } from '../_services/eventstreamapi.service';
import { ApiService } from '../_services/api.service';
import { GoogleAnalyticsService } from 'ngx-google-analytics';
import { MockGoogleAnalyticsService } from '../_services/google-analytics.service.mock';
import { of } from 'rxjs/internal/observable/of';
import { MockTestApiService } from '../_services/api.service.test.mock';
import { MockEventStreamApiService } from '../_services/eventstreamapi.service.mock';

describe('Georeference component with complex data to load', () => {
  let comp: GeoreferenceComponent;
  let fixture: ComponentFixture<GeoreferenceComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [...app_declarations],
      imports: [...app_imports],
      providers: [
        GeoreferenceComponent,
        { provide: ApiService, useClass: MockTestApiService },
        { provide: EventStreamApiService, useClass: MockEventStreamApiService },
        {
          provide: GoogleAnalyticsService,
          useClass: MockGoogleAnalyticsService,
        },
        {
          provide: ActivatedRoute,
          useValue: {
            fragment: of(''),
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

  beforeEach(async end => {
    fixture = TestBed.createComponent(GeoreferenceComponent);
    comp = fixture.componentInstance;
    comp.plan_id = '1';
    await comp.loadData();
    await fixture.whenStable();
    end();
  });
  afterEach(() => {
    document.body.removeChild(fixture.debugElement.nativeElement);
  });

  it('should create component', () => expect(comp).toBeDefined());

  it('should be able to center the map, meaning that Open layers worked well', () => {
    comp.centerMap();
    expect(comp).toBeDefined();
  });
});
