import type { LngLat, SupportedRegion } from '../types/api';

export interface RegionDefinition {
  code: SupportedRegion;
  label: string;
  center: LngLat;
  bbox: readonly [number, number, number, number];
}

export const regions: Record<SupportedRegion, RegionDefinition> = {
  seoul: {
    code: 'seoul',
    label: '서울',
    center: { lng: 127.1001, lat: 37.5133 },
    bbox: [126.76, 37.41, 127.18, 37.7],
  },
  cheongju: {
    code: 'cheongju',
    label: '청주',
    center: { lng: 127.489, lat: 36.6424 },
    bbox: [127.25, 36.45, 127.75, 36.85],
  },
};

export const regionOptions = Object.values(regions);

export function isPointInRegion(point: LngLat, regionCode: SupportedRegion): boolean {
  const [minLng, minLat, maxLng, maxLat] = regions[regionCode].bbox;
  return point.lng >= minLng && point.lng <= maxLng && point.lat >= minLat && point.lat <= maxLat;
}

export function inferRegion(point: LngLat): SupportedRegion | null {
  return regionOptions.find((region) => isPointInRegion(point, region.code))?.code ?? null;
}
