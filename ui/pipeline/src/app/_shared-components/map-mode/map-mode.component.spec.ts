import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { app_declarations } from '../../app.declarations';
import { app_imports } from '../../app.imports';
import { MapModeComponent } from './map-mode.component';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

describe('Map mode component', () => {
  let comp: MapModeComponent;
  let fixture: ComponentFixture<MapModeComponent>;
  let changeMapSelect: DebugElement;
  let changeMapOption: DebugElement;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [...app_declarations],
      imports: [...app_imports],
      providers: [MapModeComponent],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MapModeComponent);
    comp = fixture.componentInstance;
  });
  afterEach(() => {
    document.body.removeChild(fixture.debugElement.nativeElement);
  });

  it('should create component', () => {
    expect(comp).toBeDefined();
  });

  it('should have a select with options', () => {
    changeMapSelect = fixture.debugElement.query(By.css('#changeMapId'));
    expect(changeMapSelect).toBeDefined();

    changeMapOption = fixture.debugElement.query(By.css('#changeMapId option'));
    expect(changeMapOption).toBeDefined();
  });
});
