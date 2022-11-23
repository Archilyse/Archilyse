import { AppComponent } from './app.component';
import { ClassificationComponent } from './classification/classification.component';
import { FloorplanEditorComponent } from './_shared-components/floorplan/floorplan-editor.component';
import { HelpDialogClassificationComponent } from './classification/help-classification/help-classification.component';
import { SplittingComponent } from './splitting/splitting.component';
import { HelpDialogSplittingComponent } from './splitting/help-splitting/help-splitting.component';
import { HelpDialogGeoreferenceComponent } from './georeference/help-georeference/help-georeference.component';
import { GeoreferenceComponent } from './georeference/georeference.component';
import { FooterComponent } from './_shared-components/footer/footer.component';
import { SaveAndHelpComponent } from './_shared-components/save-and-help/save-and-help.component';
import { LoginComponent } from './login/login.component';
import { InfoBoxOverlayComponent } from './_shared-components/info-box-overlay/info-box-overlay.component';
import { FloorplanHeatmapLegendComponent } from './_shared-components/floorplan-heatmap/floorplan-heatmap-legend.component';
import { MapModeComponent } from './_shared-components/map-mode/map-mode.component';
import { LinkingComponent } from './linking/linking.component';
import { HelpDialogLinkingComponent } from './linking/help-linking/help-linking.component';
import { HelpDialogQualityComponent } from './quality/help-quality/help-quality.component';
import { NavigationComponent } from './_shared-components/navigation/navigation.component';
import { QualityComponent } from './quality/quality.component';
import { NavigationSiteComponent } from './_shared-components/navigation-site/navigation-site.component';
import { UnitQaComponent } from './_shared-components/unit-qa/unit-qa.component';
import { LogOutComponent } from './_shared-components/log-out/log-out.component';
import { QualityCheckBoxComponent } from './_shared-components/quality-check-box/quality-check-box.component';
import { BrooksErrorsComponent } from './_shared-components/brooks-errors/brooks-errors.component';

export const app_declarations = [
  AppComponent,
  BrooksErrorsComponent,
  GeoreferenceComponent,
  ClassificationComponent,
  SplittingComponent,
  FloorplanEditorComponent,
  UnitQaComponent,
  NavigationSiteComponent,
  HelpDialogGeoreferenceComponent,
  HelpDialogClassificationComponent,
  HelpDialogLinkingComponent,
  HelpDialogSplittingComponent,
  HelpDialogQualityComponent,
  InfoBoxOverlayComponent,
  FloorplanHeatmapLegendComponent,
  FooterComponent,
  SaveAndHelpComponent,
  NavigationSiteComponent,
  MapModeComponent,
  LinkingComponent,
  LoginComponent,
  NavigationComponent,
  QualityComponent,
  LogOutComponent,
  QualityCheckBoxComponent,
];
