import { AppRoutingModule } from './app-routing.module';

import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgxPopperModule } from 'ngx-popper';
import { MatFormFieldModule } from '@angular/material/form-field';
import { NgxGoogleAnalyticsModule } from 'ngx-google-analytics';
import { environment } from '../environments/environment';

export const app_imports = [
  BrowserModule,
  AppRoutingModule,
  HttpClientModule,
  BrowserAnimationsModule,
  MatDialogModule,
  MatSnackBarModule,
  FormsModule,
  MatFormFieldModule,
  NgxPopperModule.forRoot({
    placement: 'top',
    trigger: 'hover',
    showDelay: 500,
    hideOnScroll: true,
    applyClass: 'arch',
  }),
  ReactiveFormsModule,
  NgxGoogleAnalyticsModule.forRoot(environment.googleTrackingId),
];
