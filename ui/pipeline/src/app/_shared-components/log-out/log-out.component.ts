import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { LocalStorage } from '../../_shared-libraries/LocalStorage';

@Component({
  selector: 'app-log-out',
  templateUrl: './log-out.component.html',
  styleUrls: ['./log-out.component.scss'],
})
export class LogOutComponent implements OnInit {
  constructor(private router: Router) {}

  ngOnInit() {}

  logOut() {
    LocalStorage.deleteApiToken();
    this.router.navigate(['/login', { previousUrl: this.router.url }]);
  }
}
