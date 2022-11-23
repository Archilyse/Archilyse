import { Component, Input, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { NavigationConstants } from '../../_shared-libraries/NavigationConstants';
import { ApiService } from '../../_services/api.service';
import { EditorService } from '../../_services/editor.service';
import { hasOwnNestedProperty } from '../../_shared-libraries/Validations';
import { UiService } from '../../_services/ui.service';

@Component({
  selector: 'app-navigation',
  templateUrl: './navigation.component.html',
  styleUrls: ['./navigation.component.scss'],
})
export class NavigationComponent implements OnInit {
  @Input() saveDisabled;

  tabActive;
  navigationEnabled = true;
  plan_id;
  app_status;

  constructor(
    private router: Router,
    private activatedRoute: ActivatedRoute,
    private snackBar: MatSnackBar,
    private apiService: ApiService,
    private editorService: EditorService,
    private uiService: UiService
  ) {
    if (hasOwnNestedProperty(this.activatedRoute, 'snapshot.params')) {
      const params = this.activatedRoute.snapshot.params;
      this.plan_id = params.plan_id;
    }
    if (hasOwnNestedProperty(this.activatedRoute, 'snapshot.url') && this.activatedRoute.snapshot.url.length > 0) {
      this.tabActive = this.activatedRoute.snapshot.url[0].path;
    }
    this.app_status = this.apiService.status;
  }

  goToNewEditor() {
    window.open(`/v2/editor/${this.plan_id}`);
  }

  ngOnInit(): void {}
  navigateTo(event, page, status) {
    event.preventDefault();

    if (status !== NavigationConstants.APP_ACTIVE) {
      if (status !== NavigationConstants.APP_DISABLED) {
        if (this.plan_id) {
          if (this.confirmToLink()) {
            this.editorService.resetValuesForNavigation();
            this.uiService.resetValuesForNavigation();
            if (page === 'editor') {
              this.goToNewEditor();
            } else {
              this.router.navigate([page, this.plan_id]);
            }
          }
        } else {
          this.showWarning('Plan ID is not defined.');
        }
      } else {
        const prerequisiteSequence = { splitting: 'georeferencing', linking: 'splitting' };
        if (Object.keys(prerequisiteSequence).includes(page)) {
          this.showWarning(`In order to do the ${page}, the ${prerequisiteSequence[page]} must be done first.`);
        } else {
          this.showWarning(`In order to proceed to ${page} make sure that previous steps have been completed.`);
        }
      }
    }
  }

  confirmToLink() {
    return this.saveDisabled || confirm('You have unsaved work, Are you sure?');
  }

  isTabActive(phaseName) {
    return { active: this.tabActive === phaseName };
  }

  getTabStatus(phaseName) {
    const tabStatus = this.app_status[phaseName];
    return {
      disabled: tabStatus === NavigationConstants.APP_DISABLED,
      completed: tabStatus === NavigationConstants.APP_COMPLETED,
      active: tabStatus === NavigationConstants.APP_ACTIVE,
      available: tabStatus === NavigationConstants.APP_AVAILABLE,
    };
  }

  showWarning(message) {
    this.snackBar.open(message, 'Okay', {
      duration: 0,
    });
  }
}
