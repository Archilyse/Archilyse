import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { ClassificationComponent } from './classification/classification.component';
import { SplittingComponent } from './splitting/splitting.component';
import { GeoreferenceComponent } from './georeference/georeference.component';
import { LinkingComponent } from './linking/linking.component';
import { LoginComponent } from './login/login.component';
import { QualityComponent } from './quality/quality.component';

const routes: Routes = [
  { path: 'linking/:plan_id', component: LinkingComponent },
  { path: 'splitting/:plan_id', component: SplittingComponent },
  {
    path: 'classification/:plan_id',
    component: ClassificationComponent,
  },
  { path: 'login', component: LoginComponent },
  { path: 'quality/:site_id', component: QualityComponent },
  {
    path: 'georeference/:plan_id',
    component: GeoreferenceComponent,
  },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule {}
