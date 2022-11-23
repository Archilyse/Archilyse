import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { app_declarations } from '../../app.declarations';
import { app_imports } from '../../app.imports';
import { ActivatedRoute } from '@angular/router';
import { NavigationComponent } from './navigation.component';
import { ApiService } from '../../_services/api.service';
import { MockApiService } from '../../_services/api.service.mock';

describe('Navigation component', () => {
  let comp: NavigationComponent;
  let fixture: ComponentFixture<NavigationComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [...app_declarations],
      imports: [...app_imports],
      providers: [
        NavigationComponent,
        { provide: ApiService, useClass: MockApiService },
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
    fixture = TestBed.createComponent(NavigationComponent);
    comp = fixture.componentInstance;
  });
  afterEach(() => {
    document.body.removeChild(fixture.debugElement.nativeElement);
  });

  it('should create component', () => expect(comp).toBeDefined());
});
