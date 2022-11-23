import { Component, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { EditorService } from '../../_services/editor.service';
import { ApiService } from '../../_services/api.service';
import { ActivatedRoute, Router } from '@angular/router';
import { buildFloorArrayToDisplay, floorsToArray } from '../../_shared-libraries/FloorFormat';
import { BaseComponent } from '../../base.component';
import { UiService } from '../../_services/ui.service';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-navigation-site',
  templateUrl: './navigation-site.component.html',
  styleUrls: ['./navigation-site.component.scss'],
})
export class NavigationSiteComponent extends BaseComponent implements OnInit, OnChanges {
  @Input() siteId;
  @Input() planId;
  @Input() saveDisabled;

  site;
  building;
  floor;

  buildings;
  floors;
  floorsToDisplay;

  constructor(
    private apiService: ApiService,
    private uiService: UiService,
    private editorService: EditorService,
    private activatedRoute: ActivatedRoute,
    private router: Router
  ) {
    super();
  }

  ngOnInit(): void {}

  ngOnChanges(changes: SimpleChanges): void {
    this.loadData();
  }

  async loadData() {
    this.error = null;
    this.loading = true;

    try {
      if (this.siteId) {
        this.site = await this.apiService.getSiteBuildingAndFloors(this.siteId);
        this.loadSiteData(this.site);
      }
    } catch (e) {
      this.parseError(e);
    }
  }

  /**
   * Given the structure of a given site loads the buildings and floors
   * @param site
   */
  loadSiteData(site) {
    if (site) {
      if (site.client_site_id) {
        this.client_site_id = site.client_site_id;
      }
      if (site.buildings && site.buildings.length) {
        this.buildings = site.buildings;
        this.building = this.findCurrentBuilding(this.buildings, `${this.planId}`);
        if (this.building) {
          this.floors = floorsToArray(this.building.floors);
          this.floorsToDisplay = buildFloorArrayToDisplay(this.floors);
          this.floor = this.floors.find(p => `${p.plan_id}` === `${this.planId}`);
          this.loading = false;
        }
      } else {
        throw new Error('Current site has no buildings');
      }
    }
  }

  /**
   * From the given buildings list finds the one that has a floor with the given planId
   * @param buildings
   * @param planId
   */
  findCurrentBuilding(buildings, planId: string) {
    return buildings.find(b => {
      if (b.floors) {
        return floorsToArray(b.floors).some(floor => `${floor.plan_id}` === planId);
      }
      return false;
    });
  }

  confirmToLink() {
    return this.saveDisabled || confirm('You have unsaved work, Are you sure?');
  }
  linkToSite() {
    if (this.confirmToLink()) {
      // URL to the admin tool
      location.replace(`${environment.adminBuildingsUrl}${this.siteId}`);
    }
  }

  /**
   * User changes the building, so we change the floor to the new building.
   * Same FloorNr if it exists or first if not.
   * @param building
   */
  linkToBuilding(building) {
    const floors = floorsToArray(building.floors);

    if (floors && floors.length) {
      // We find a the same floorNr in the other building.
      const newFloor = floors.find(f => f.floor_number === this.floor.floor_number);
      if (newFloor) {
        this.linkToPlan(newFloor.plan_id);
      } else {
        // Otherwise we take the first floor
        this.linkToPlan(floors[0].plan_id);
      }
    } else {
      console.error('Building has no floors');
    }
  }

  /**
   * User navigates to the same page but with another plan
   * @param plan_id
   */
  linkToPlan(plan_id) {
    const num_expected_parameters_url = 2;
    if (this.activatedRoute.snapshot.url.length === num_expected_parameters_url) {
      if (this.confirmToLink()) {
        const url = this.activatedRoute.snapshot.url.map(segment => segment.path);
        url[1] = `${plan_id}`;

        this.editorService.resetValuesForNavigation();
        this.uiService.resetValuesForNavigation();
        this.router.navigate(url);
      }
    }
  }

  /**
   * User changes the select with buildings
   * @param event
   */
  onChangeBuilding(event) {
    const buildingId = event.target.value;
    const building = this.buildings.find(b => `${b.id}` === buildingId);
    if (building) {
      this.linkToBuilding(building);
    }
  }

  /**
   * User changes the select with floors
   * @param event
   */
  onChangePlan(event) {
    const plan_id = event.target.value;
    this.linkToPlan(plan_id);
  }

  /**
   * Cuts the string and adds ... to it when reached the specified length
   * (Used to protect long strings in FE)
   * @param originalString
   * @param len
   */
  cutString(originalString: string, len: number) {
    if (originalString) {
      if (originalString.length > len - 3) {
        return `${originalString.slice(0, len - 3)}...`;
      }
      return originalString;
    }
    return '';
  }
}
