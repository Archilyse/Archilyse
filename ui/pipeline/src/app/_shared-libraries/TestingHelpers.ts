import { DebugElement } from '@angular/core';
import { By } from '@angular/platform-browser';

export class TestingHelpers {
  public static keyDown(fixture, keyX) {
    const xEventDown: any = document.createEvent('CustomEvent');
    xEventDown.which = keyX;
    xEventDown.initEvent('keydown', true, true);
    document.dispatchEvent(xEventDown);
    fixture.detectChanges();
  }

  public static keyUp(fixture, keyX) {
    const xEventUp: any = document.createEvent('CustomEvent');
    xEventUp.which = keyX;
    xEventUp.initEvent('keyup', true, true);
    document.dispatchEvent(xEventUp);
    fixture.detectChanges();
  }

  /**
   * Validating that all the apps have a help dialog explaining how they work.
   * @param expect
   * @param fixture
   * @param end
   */
  public static testHelpButtonWithDialog(expect, fixture, end) {
    let error;
    fixture.detectChanges();
    fixture.whenStable().then(() => {
      const helpButton: DebugElement = fixture.debugElement.query(By.css('#help_button'));
      helpButton.triggerEventHandler('click', null);

      error = 'No help button defined';
      expect(helpButton).toBeDefined(error);
      expect(helpButton).not.toBeNull(error);
      fixture.detectChanges();
      fixture.whenStable().then(() => {
        const helpDialog = document.getElementById('helpDialog');

        error = 'No help dialog defined';
        expect(helpDialog).toBeDefined(error);
        expect(helpDialog).not.toBeNull(error);

        // Press Esc to close.
        const keyEsc = 27;
        TestingHelpers.keyDown(fixture, keyEsc);
        TestingHelpers.keyUp(fixture, keyEsc);

        end();
      });
    });
  }

  /**
   * Validate that the saving button is disabled by default
   * and only enabled when the content changed.
   * @param expect
   * @param comp
   * @param fixture
   */
  public static testSaveButtonOnlyWhenModified(expect, comp, fixture) {
    fixture.detectChanges();
    const saveButton = document.getElementById('save_button');
    expect(saveButton['disabled']).toBe(true);
    expect(saveButton.innerText).toBe('Saved');

    expect(comp.contentChanged).toBeDefined('Method contentChanged should be defined');

    // We trigger the method that marks the content as changed in the component
    comp.contentChanged();

    fixture.detectChanges();
    expect(saveButton['disabled']).toBe(false, `Save button shoudn't be disabled after contentChanged was called`);
    expect(saveButton.innerText).toBe('Save');
  }

  /**
   * Validate that the components display an error in the screen
   * when a captured exception is thrown
   * @param expect
   * @param comp
   * @param fixture
   */
  public static testDisplayErrorInComponent(expect, comp, fixture) {
    const errorMessageStr = 'Artificial error';

    // Default data
    comp.loading = false;
    comp.plan_id = '1';
    comp.site_id = '1';

    fixture.detectChanges();

    expect(comp.parseError).toBeDefined('Method parseError should be defined');
    comp.parseError(new DOMException(errorMessageStr));

    fixture.detectChanges();
    // In the component:
    expect(comp.error).toBe(errorMessageStr);

    // Displayed in the dom
    const errorMessage = document.getElementById('errorMessage');
    expect(errorMessage.innerText).toBe(errorMessageStr);
  }

  /**
   * Validate that the footer is displayed, used in all the apps.
   * @param expect
   * @param copyright
   * @param fixture
   */
  public static checkArchilyseFooter(expect, copyright, fixture) {
    fixture.detectChanges();
    const copyrightDiv = copyright.nativeElement;
    expect(copyrightDiv.innerText).toMatch(/Archilyse/i, '<h1> should say Archilyse');
  }
}
