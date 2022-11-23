import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { NavigationSiteComponent } from './navigation-site.component';
import { app_declarations } from '../../app.declarations';
import { app_imports } from '../../app.imports';
import { ApiService } from '../../_services/api.service';
import { MockApiService } from '../../_services/api.service.mock';

describe('Navigation Site component', () => {
  let comp: NavigationSiteComponent;
  let fixture: ComponentFixture<NavigationSiteComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [...app_declarations],
      imports: [...app_imports],
      providers: [{ provide: ApiService, useClass: MockApiService }, NavigationSiteComponent],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(NavigationSiteComponent);
    comp = fixture.componentInstance;
    comp.siteId = 1;
    comp.planId = 1;
  });
  afterEach(() => {
    document.body.removeChild(fixture.debugElement.nativeElement);
  });

  it('should create component', () => expect(comp).toBeDefined());
});
