import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { app_declarations } from '../../app.declarations';
import { app_imports } from '../../app.imports';
import { QualityCheckBoxComponent } from './quality-check-box.component';
import { ApiService } from '../../_services/api.service';
import { MockApiService } from '../../_services/api.service.mock';

function assertClosed(fixture) {
  const saveNotes = fixture.debugElement.query(By.css('#save_notes_button'));
  const textArea = fixture.debugElement.query(By.css('textarea'));
  const qualityLabel = fixture.debugElement.query(By.css('.qualityLabel'));

  expect(qualityLabel).not.toBeNull();

  expect(saveNotes).toBeNull();
  expect(textArea).toBeNull();
}
function assertOpen(fixture) {
  const saveNotes = fixture.debugElement.query(By.css('#save_notes_button'));
  const textArea = fixture.debugElement.query(By.css('textarea'));

  expect(saveNotes).not.toBeNull();
  expect(textArea).not.toBeNull();
}

describe('Check quality component', () => {
  let comp: QualityCheckBoxComponent;
  let fixture: ComponentFixture<QualityCheckBoxComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [...app_declarations],
      imports: [...app_imports],
      providers: [QualityCheckBoxComponent, { provide: ApiService, useClass: MockApiService }],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(QualityCheckBoxComponent);
    comp = fixture.componentInstance;
  });

  it('should create component', () => expect(comp).toBeDefined());
  it('should properly display a closed component', () => {
    comp.site_id = 1;
    comp.always_open = false;
    fixture.detectChanges();
    assertClosed(fixture);
  });

  it('should properly display an open component', () => {
    comp.site_id = 1;
    comp.always_open = true;
    fixture.detectChanges();
    assertOpen(fixture);
  });

  it('should properly display a closed component and then open it and close again', () => {
    comp.site_id = 1;
    comp.always_open = false;
    fixture.detectChanges();
    assertClosed(fixture);
    comp.toggle();
    fixture.detectChanges();
    assertOpen(fixture);
    comp.toggle();
    fixture.detectChanges();
    assertClosed(fixture);
  });

  it('should properly check if the text displayed is correct', async end => {
    comp.site_id = 1;
    comp.always_open = true;
    await comp.getSiteData();
    fixture.detectChanges();
    expect(comp.validation_notes).toBe('Example validation');
    end();
  });
});
