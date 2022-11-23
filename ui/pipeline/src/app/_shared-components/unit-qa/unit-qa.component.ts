import { Component, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { ApiService } from '../../_services/api.service';
import { environment } from '../../../environments/environment';

const _qaLocalCache = {};

@Component({
  selector: 'app-unit-qa',
  templateUrl: './unit-qa.component.html',
  styleUrls: ['./unit-qa.component.scss'],
})
export class UnitQaComponent implements OnInit, OnChanges {
  @Input() unit;
  @Input() site_id;

  loading;
  notProvided;
  correct;

  plan_id;
  client_id;
  area_ids;

  warnings;
  warningsStr;
  errorsStr;

  corrects;
  correctsStr;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.calculateWarings();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.unit && !changes.unit.firstChange) {
      this.calculateWarings();
    }
  }

  /**
   *  Calculates all the warnings to display for the given unit
   */
  async calculateWarings() {
    // We reset the warning every time
    this.loading = true;
    this.notProvided = false;
    this.warnings = null;
    this.warningsStr = '';
    this.errorsStr = '';

    this.corrects = null;
    this.correctsStr = '';

    try {
      this.client_id = this.getUnitDataAndClientId();
      if (this.client_id) {
        const qaData = await this.requestQaAndCheckUnitClientId(this.client_id);
        // Validations of area and rooms
        this.checkArea(qaData);
        this.checkNumberOfRooms(qaData);
        this.loading = false;
      } else {
        this.notFound();
      }
    } catch (e) {
      console.error(e);
      this.loading = false;
      this.errorsStr = 'The request for QA data failed, try again or contact support';
      return;
    }

    if (this.warnings) {
      this.warningsStr = this.warnings.join(`<br/>`);
    } else if (!this.notProvided) {
      this.correct = true;
      this.correctsStr = this.corrects ? this.corrects.join(`<br/>`) : '';
    }
  }

  notFound() {
    this.loading = false;
    this.notProvided = true;
  }

  addWarning(message) {
    if (!this.warnings) {
      this.warnings = [];
    }
    this.warnings.push(message);
  }

  addCorrect(message) {
    if (!this.corrects) {
      this.corrects = [];
    }
    this.corrects.push(message);
  }

  /**
   * We need to check if the unit has a client Id.
   */
  getUnitDataAndClientId() {
    if (this.unit && this.unit.client_id) {
      this.plan_id = this.unit.plan_id;
      this.area_ids = this.unit.area_ids;

      return this.unit.client_id;
    }
    return null;
  }

  /**
   * We request the QA data for this site and try to find this particular client Id there.
   * @param client_id
   */
  async requestQaAndCheckUnitClientId(client_id) {
    if (_qaLocalCache[client_id]) {
      return _qaLocalCache[client_id];
    }

    const siteQaData = await this.api.getSiteQa(this.site_id);
    if (siteQaData?.data?.[client_id]) {
      // We store the data in the local cache to avoid extra requests
      _qaLocalCache[client_id] = siteQaData.data[client_id];
      return siteQaData.data[client_id];
    }
    return null;
  }

  /**
   * Checks that the qaData data matches the unit Area in m2
   * Adds the warning if needed
   * @param qaData
   */
  async checkArea(qaData) {
    if (qaData && (typeof qaData.HNF !== 'undefined' || typeof qaData.net_area !== 'undefined')) {
      if (this.unit.m2) {
        const m2 = parseInt(this.unit.m2, 10);
        const expectedM2 = parseInt(qaData.HNF ? qaData.HNF : qaData.net_areas, 10);

        const ratio = m2 / expectedM2;
        const ratioError = Math.abs(ratio - 1);

        if (ratioError > environment.qaErrorMarginM2) {
          this.addWarning(
            `Net area doesn't match: Current value ${m2}m<sup>2</sup> expected ${expectedM2}m<sup>2</sup>`
          );
        } else {
          this.addCorrect(`Net area ${m2}m<sup>2</sup> expected ${expectedM2}m<sup>2</sup>`);
        }
      }
    } else {
      this.notFound();
    }
  }

  /**
   * Checks that the qaData data matches the unit rooms
   * Adds the warning if needed
   * @param qaData
   */
  async checkNumberOfRooms(qaData) {
    if (qaData && qaData.number_of_rooms) {
      if (this.unit.rooms) {
        const rooms = parseFloat(this.unit.rooms);
        const expectedRooms = parseFloat(qaData.number_of_rooms);
        const error = Math.abs(rooms - expectedRooms);

        if (error > environment.qaErrorMarginRooms) {
          this.addWarning(`Number of rooms doesn't match: Current value ${rooms} expected ${expectedRooms}`);
        } else {
          this.addCorrect(`Number of rooms ${rooms} expected ${expectedRooms}`);
        }
      }
    }
  }
}
