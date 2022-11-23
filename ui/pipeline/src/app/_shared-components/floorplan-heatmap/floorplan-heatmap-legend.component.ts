import { Component, Input, OnChanges, SimpleChanges, AfterViewInit, OnDestroy } from '@angular/core';

import * as d3 from 'd3';
import { Subscription } from 'rxjs/internal/Subscription';
import { getHexColorsAndLegend, correctScale } from '../../_shared-libraries/SimData';

@Component({
  selector: 'app-floorplan-heatmap-legend',
  templateUrl: './floorplan-heatmap-legend.component.html',
  styleUrls: ['./floorplan-heatmap-legend.component.scss'],
})
export class FloorplanHeatmapLegendComponent implements AfterViewInit, OnChanges, OnDestroy {
  /** Id of the element to be mounted*/
  @Input() legendId;

  /** Matrix with all the hexagon values */
  @Input() hexData;

  /** Value to color function */
  @Input() color;

  /** Unit of the current hexagon values */
  @Input() unit;

  /** Minimum value of the current range */
  @Input() min;
  /** Maximum  value of the current range */
  @Input() max;

  @Input() isCompare;

  bins;
  data;
  _drawHistogramPlot;
  uniqueId;
  subscription: Subscription;

  rangeScaleWrapper;
  rangeWrapper;
  rangeMin;
  rangeMax;
  rangeUnitWrapper;

  increments = [];
  rangeSelection = [];

  container;
  width;

  /** We multiply the displayed value by the scale */
  scale;

  constructor() {}

  ngOnDestroy() {
    // prevent memory leak when component destroyed
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }

  ngOnChanges(changes: SimpleChanges) {
    if ((changes.min && !changes.min.firstChange) || (changes.max && !changes.max.firstChange)) {
      this._drawHistogramPlot = null;
      this.setUpDiagram();
    } else if (changes.hexData && !changes.hexData.firstChange) {
      this.plot(this.hexData);
    }
  }

  ngAfterViewInit() {
    this.container = document.getElementById(this.legendId);
    this.width = this.container.offsetWidth;
    this.setUpDiagram();
  }

  setUpDiagram() {
    const colorsAndLegend = getHexColorsAndLegend(this.hexData, this.min, this.max, 9);
    const legend = colorsAndLegend.legend;

    this.bins = Object.keys(legend);
    this.data = this.bins.map(key => legend[key]);

    // Information provided in Klux, so when the unit is lux we multiply by 10;
    this.scale = correctScale(this.unit);

    this.rangeMin = d3.select(`#${this.legendId}`).selectAll('*').remove();

    this.rangeScaleWrapper = d3
      .select(`#${this.legendId}`)
      .append('div')
      .attr('class', 'range-scale-wrapper')
      .attr('id', 'rangeScaleWrapper');

    this.rangeUnitWrapper = d3
      .select(`#${this.legendId}`)
      .append('div')
      .attr('class', 'range-unit-wrapper')
      .attr('id', 'rangeUnitWrapper')
      .html(this.unit);

    // create the div that will hold the minimum value
    this.rangeMin = this.rangeScaleWrapper
      .append('div')
      .attr('class', 'range-extreme')
      .attr('id', 'rangeMin')
      .text(() => {
        if (this.isCompare) {
          // Only absolute values in compare mode.
          return -Math.round(this.min * this.scale);
        }
        return Math.round(this.min * this.scale);
      });

    // create the div that will wrap the color range
    this.rangeWrapper = this.rangeScaleWrapper.append('div').attr('class', 'range-wrapper');

    // create the div that will hold the maximum value
    this.rangeMax = this.rangeScaleWrapper
      .append('div')
      .attr('class', 'range-extreme')
      .attr('id', 'rangeMax')
      .text(Math.round(this.max * this.scale));

    d3.select(`#${this.legendId}`).on('click', () => {
      if (this.rangeSelection.length > 1) {
        this.removeSelection();
      }
    });

    this.plot(this.data);
  }

  plot(data) {
    if (this.data?.length > 0) {
      this._drawHistogramPlot = this.rangeWrapper.data(data).call(this.drawHeatmapLegend, this);
    }
  }

  drawHeatmapLegend(selection, _this) {
    d3.select(`#range`).remove();
    const range = selection.append('div').attr('class', 'range').attr('id', 'range');

    _this.bins.map((a, i) => {
      range
        .append('div')
        .attr('index', Math.floor(i))
        .attr('class', 'increment')
        .style('background-color', _this.color[i])
        .on('click', function () {
          d3.event.stopPropagation();
          _this.onClick(this);
        })
        .on('mouseover', function () {
          _this.mouseEnter(this);
        })
        .on('mouseout', function () {
          _this.mouseExit(this);
        });
    });

    _this.increments = Array.from(d3.selectAll(`.increment`)._groups[0]);
  }

  mouseEnter(svgColumn) {
    // const index = parseInt(svgColumn.getAttribute('index'), 10);
    // const data = this.bins[index];
    // const foo = {
    //   min: data,
    //   current: data,
    //   max: null,
    // };
    // this.diagramService.eventFired(this.uniqueId, foo);
  }

  mouseExit() {
    // this.diagramService.noEventFired(this.uniqueId);
  }

  removeSelection() {
    this.rangeSelection = [];
    this.increments.forEach(el => el.classList.remove('selected'));
    this.increments.forEach(el => el.classList.remove('range-active'));
  }

  onClick(event) {
    const clickEnabled = false;
    if (clickEnabled) {
      if (this.rangeSelection.length < 1) {
        // this.rangeUnitWrapper.html('Select another value for the range');
      }

      if (this.rangeSelection.length === 1) {
        this.rangeUnitWrapper.html(this.unit);
      }

      if (this.rangeSelection.length > 1) {
        this.removeSelection();
        return;
      }

      this.rangeSelection = [...this.rangeSelection.splice(-1), event];

      this.constructSelectedRange(this.rangeSelection);

      event.classList.add('selected');
    }
  }

  constructSelectedRange(selected) {
    if (selected.length < 2) {
      return;
    }

    const indexes = selected.map(el => this.increments.indexOf(el)).sort();

    this.increments.forEach((el, i) => {
      if (i >= indexes[0] && i <= indexes[1]) {
        el.classList.add('selected');
      } else {
        el.classList.add('range-active');
      }
    });

    return {
      min: this.bins[indexes[0]],
      current: null,
      max: this.bins[indexes[1]],
    };
  }
}
