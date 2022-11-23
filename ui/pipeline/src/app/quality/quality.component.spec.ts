import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { DebugElement } from '@angular/core';
import { By } from '@angular/platform-browser';
import { app_declarations } from '../app.declarations';
import { app_imports } from '../app.imports';
import { ActivatedRoute } from '@angular/router';
import { TestingHelpers } from '../_shared-libraries/TestingHelpers';
import { ApiService } from '../_services/api.service';
import { MockApiService } from '../_services/api.service.mock';
import { QualityComponent } from './quality.component';
import { GoogleAnalyticsService } from 'ngx-google-analytics';
import { MockGoogleAnalyticsService } from '../_services/google-analytics.service.mock';

describe('Quality component', () => {
  let copyright: DebugElement;
  let cardTitle: DebugElement;
  let comp: QualityComponent;
  let fixture: ComponentFixture<QualityComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [...app_declarations],
      imports: [...app_imports],
      providers: [
        QualityComponent,
        {
          provide: GoogleAnalyticsService,
          useClass: MockGoogleAnalyticsService,
        },
        { provide: ApiService, useClass: MockApiService },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              params: {
                site_id: '1',
              },
            },
          },
        },
      ],
    });
  }));

  beforeEach(async end => {
    fixture = TestBed.createComponent(QualityComponent);
    comp = fixture.componentInstance;
    comp.site_id = '1';
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

  it('should have copyright list', () => {
    TestingHelpers.checkArchilyseFooter(expect, copyright, fixture);
  });
});
