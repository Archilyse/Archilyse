import { buildFloorArrayToDisplay, floorToHumanStr, getRangesHuman, groupFloorsInRanges, nth } from './FloorFormat';

const example_floors = [
  {
    plan_id: 1,
    floor_number: -1,
  },
  {
    plan_id: 1,
    floor_number: 0,
  },
  {
    plan_id: 1,
    floor_number: 2,
  },
  {
    plan_id: 2,
    floor_number: 1,
  },
];

describe('FloorFormat.ts library', () => {
  beforeEach(() => {});

  it('should properly generate the ordinals', () => {
    expect(nth(-1)).toBe('th');
    expect(nth(0)).toBe('th');
    expect(nth(1)).toBe('st');
    expect(nth(2)).toBe('nd');
    expect(nth(3)).toBe('rd');
    expect(nth(4)).toBe('th');
    expect(nth(100)).toBe('th');
  });

  it('should properly generate the human readable floor strings', () => {
    expect(floorToHumanStr(-1)).toBe('-1 UG');
    expect(floorToHumanStr(0)).toBe('Ground floor');
    expect(floorToHumanStr(1)).toBe('1st floor');
    expect(floorToHumanStr(2)).toBe('2nd floor');
    expect(floorToHumanStr(3)).toBe('3rd floor');
    expect(floorToHumanStr(4)).toBe('4th floor');
    expect(floorToHumanStr(100)).toBe('100th floor');
  });

  it('should properly generate the human readable floor ranges', () => {
    expect(getRangesHuman([-1, 0, 1, 2, 7, 10, 11, 12])).toEqual([
      '-1 UG to 2nd floor',
      '7th floor',
      '10th floor to 12th floor',
    ]);
  });
  it('should properly generate the human readable floor', () => {
    const result = buildFloorArrayToDisplay(example_floors);
    expect(result[0].floor_numbers).toBe('-1 UG to Ground floor, 2nd floor');
    expect(result[1].floor_numbers).toBe('1st floor');
  });
  it('should properly generate the human readable floor ranges', () => {
    const result = groupFloorsInRanges(example_floors);
    expect(result[1].length).toBe(3);
    expect(result[2].length).toBe(1);
  });
});
