import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { app_declarations } from '../app.declarations';
import { app_imports } from '../app.imports';
import { LoginComponent } from './login.component';

describe('Login component', () => {
  let comp: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [...app_declarations],
      imports: [...app_imports],
      providers: [LoginComponent],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(LoginComponent);
    comp = fixture.componentInstance;
  });

  afterEach(() => {
    document.body.removeChild(fixture.debugElement.nativeElement);
  });

  it('should create component', () => expect(comp).toBeDefined());
});
