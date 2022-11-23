import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { LocalStorage } from '../_shared-libraries/LocalStorage';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ApiService } from '../_services/api.service';
import { parseErrorObj } from '../_shared-libraries/Url';
import { ActivatedRoute, Router } from '@angular/router';
import { authenticate } from '../_services/auth.interceptor';

const SUCCESSFULL_AUTH = 'Authentication successful, you can now navigate through the pipeline';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
})
export class LoginComponent {
  loginForm: FormGroup;
  snackBarDuration = 20000;

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    public snackBar: MatSnackBar,
    private router: Router,
    private activatedRoute: ActivatedRoute
  ) {
    this.loginForm = this.fb.group({
      user: ['', [Validators.required]],
      password: ['', [Validators.required]],
    });
    this.loadMetrics();
  }

  loadMetrics() {
    if (window.sa_pageview) {
      window.sa_pageview(window.location.pathname);
    }
  }

  /**
   * Set the token code (if correct) and go to previous url or show a snackbar
   */
  async onSubmit() {
    if (this.loginForm.invalid) {
      this.snackBar.open('Invalid user password', 'Okay', {
        duration: this.snackBarDuration,
      });
    } else {
      const user = this.loginForm.value.user;
      const password = this.loginForm.value.password;

      try {
        const rp = this.activatedRoute.snapshot;
        const previousLocation = rp.paramMap.get('previousUrl') || rp.queryParams.previousUrl;

        const response = await this.apiService.login(user, password, previousLocation);

        this.snackBar.open(response.msg, 'Okay', { duration: this.snackBarDuration });
        authenticate({ access_token: response.access_token, roles: response.roles });
        if (previousLocation) {
          const finalDestination = previousLocation;

          this.router.navigateByUrl(finalDestination);
        } else {
          this.snackBar.open(SUCCESSFULL_AUTH, 'Okay', { duration: this.snackBarDuration });
        }
      } catch (error) {
        this.snackBar.open(parseErrorObj(error), 'Okay', { duration: this.snackBarDuration });
      }
    }
  }
}
