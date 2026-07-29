import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { AppComponent } from './app.component';
import { ModelInventoryComponent } from './components/model-inventory/model-inventory.component';
import { DeploymentsComponent } from './components/deployments/deployments.component';
import { MonitoringComponent } from './components/monitoring/monitoring.component';

@NgModule({
  declarations: [
    AppComponent,
    ModelInventoryComponent,
    DeploymentsComponent,
    MonitoringComponent
  ],
  imports: [
    BrowserModule,
    HttpClientModule,
    FormsModule,
    ReactiveFormsModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
