import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-footer',
  templateUrl: './footer.component.html',
  styleUrls: ['./footer.component.scss'],
})
export class FooterComponent implements OnInit {
  year;

  constructor() {}

  ngOnInit() {
    const d = new Date();
    this.year = d.getFullYear();
  }
}
