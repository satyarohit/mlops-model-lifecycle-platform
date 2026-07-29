import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'MLOps Platform';
  currentTab = 'inventory';

  setTab(tab: string): void {
    this.currentTab = tab;
  }
}
