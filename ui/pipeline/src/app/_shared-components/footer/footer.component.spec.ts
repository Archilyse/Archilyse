import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { DebugElement } from '@angular/core';
import { By } from '@angular/platform-browser';
import { app_declarations } from '../../app.declarations';
import { app_imports } from '../../app.imports';
import { FooterComponent } from './footer.component';

describe('Footer component', () => {
  let copyright: DebugElement;
  let comp: FooterComponent;
  let fixture: ComponentFixture<FooterComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [...app_declarations],
      imports: [...app_imports],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FooterComponent);
    comp = fixture.componentInstance;
    copyright = fixture.debugElement.query(By.css('#copyright'));
  });
  afterEach(() => {
    document.body.removeChild(fixture.debugElement.nativeElement);
  });

  it('should create component', () => expect(comp).toBeDefined());
  it('should have a copyright', () => {
    expect(copyright).toBeDefined();
  });
});
