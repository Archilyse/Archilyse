import { AppComponent } from './app.component';
import { NgModule, ErrorHandler } from '@angular/core';
import { HelpDialogClassificationComponent } from './classification/help-classification/help-classification.component';
import { HelpDialogSplittingComponent } from './splitting/help-splitting/help-splitting.component';
import { HelpDialogQualityComponent } from './quality/help-quality/help-quality.component';
import { HelpDialogGeoreferenceComponent } from './georeference/help-georeference/help-georeference.component';
import { app_declarations } from './app.declarations';
import { app_imports } from './app.imports';
import { OverlayService } from './_services/overlay.service';
import { AuthInterceptor } from './_services/auth.interceptor';
import { InfoBoxOverlayComponent } from './_shared-components/info-box-overlay/info-box-overlay.component';
import { HelpDialogLinkingComponent } from './linking/help-linking/help-linking.component';
import { HTTP_INTERCEPTORS } from '@angular/common/http';
import { FloorplanClassificationService } from './_services/floorplan/floorplan.classification.service';
import { FloorplanScalingService } from './_services/floorplan/floorplan.scaling.service';
import { FloorplanLinkingService } from './_services/floorplan/floorplan.linking.service';
import { FloorplanSplittingService } from './_services/floorplan/floorplan.splitting.service';
import { FloorplanValidationService } from './_services/floorplan/floorplan.validation.service';
import { SentryErrorHandler } from './_services/error.service';

@NgModule({
  declarations: [...app_declarations],
  imports: [...app_imports],
  providers: [
    OverlayService,
    FloorplanClassificationService,
    FloorplanScalingService,
    FloorplanLinkingService,
    FloorplanSplittingService,
    FloorplanValidationService,
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true },
    { provide: ErrorHandler, useClass: SentryErrorHandler },
  ],
  entryComponents: [
    AppComponent,
    HelpDialogGeoreferenceComponent,
    HelpDialogSplittingComponent,
    HelpDialogQualityComponent,
    HelpDialogClassificationComponent,
    HelpDialogLinkingComponent,
    InfoBoxOverlayComponent,
  ],
  bootstrap: [AppComponent],
})
export class AppModule {}
