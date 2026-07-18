import { useEffect, useRef } from 'react';
import maplibregl, { type GeoJSONSource, type Map as MapLibreMap, type Marker } from 'maplibre-gl';
import type { Feature, LineString } from 'geojson';
import type { GeoJSONLineString, LngLat } from '../types/api';

interface Props {
  start?: LngLat | null;
  route?: GeoJSONLineString | null;
  sourceShape?: GeoJSONLineString | null;
  waypoints?: number[][];
  editable?: boolean;
  onMapClick?: (point: LngLat) => void;
  onRouteClick?: (point: LngLat) => void;
  onWaypointMove?: (index: number, point: number[]) => void;
  onWaypointSelect?: (index: number) => void;
  className?: string;
}

const styleUrl = import.meta.env.VITE_MAP_STYLE_URL || 'https://tiles.openfreemap.org/styles/liberty';

function sourceShapeOnRoute(
  source: GeoJSONLineString | null | undefined,
  route: GeoJSONLineString | null | undefined,
): GeoJSONLineString | null {
  if (!source?.coordinates.length || !route?.coordinates.length) return null;
  const lngs = route.coordinates.map((point) => point[0] ?? 0);
  const lats = route.coordinates.map((point) => point[1] ?? 0);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  return {
    type: 'LineString',
    coordinates: source.coordinates.map((point) => [
      minLng + (point[0] ?? 0) * (maxLng - minLng),
      maxLat - (point[1] ?? 0) * (maxLat - minLat),
    ]),
  };
}

function setGeoJson(map: MapLibreMap, id: string, data: GeoJSONLineString | null, paint: 'route' | 'shape') {
  const empty: Feature<LineString> = {
    type: 'Feature',
    properties: {},
    geometry: data ?? { type: 'LineString', coordinates: [] },
  };
  const existing = map.getSource(id) as GeoJSONSource | undefined;
  if (existing) {
    existing.setData(empty);
    return;
  }
  map.addSource(id, { type: 'geojson', data: empty });
  map.addLayer({
    id,
    type: 'line',
    source: id,
    paint:
      paint === 'route'
        ? { 'line-color': '#20d59b', 'line-width': 6, 'line-opacity': 0.95 }
        : {
            'line-color': '#ffcc66',
            'line-width': 3,
            'line-opacity': 0.65,
            'line-dasharray': [2, 2],
          },
  });
}

export function CourseMap({
  start,
  route,
  sourceShape,
  waypoints = [],
  editable = false,
  onMapClick,
  onRouteClick,
  onWaypointMove,
  onWaypointSelect,
  className,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const startMarkerRef = useRef<Marker | null>(null);
  const waypointMarkersRef = useRef<Marker[]>([]);
  const onMapClickRef = useRef(onMapClick);
  const onRouteClickRef = useRef(onRouteClick);
  const routeRef = useRef(route);
  const editableRef = useRef(editable);

  useEffect(() => {
    onMapClickRef.current = onMapClick;
    onRouteClickRef.current = onRouteClick;
    routeRef.current = route;
    editableRef.current = editable;
  }, [editable, onMapClick, onRouteClick, route]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: styleUrl,
      center: [127.1001, 37.5133],
      zoom: 12,
      attributionControl: false,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');
    map.addControl(
      new maplibregl.AttributionControl({
        compact: true,
        customAttribution: '© OpenStreetMap contributors',
      }),
      'bottom-right',
    );
    map.on('click', (event) => {
      const point = { lng: event.lngLat.lng, lat: event.lngLat.lat };
      if (editableRef.current && routeRef.current && onRouteClickRef.current) {
        onRouteClickRef.current(point);
      } else {
        onMapClickRef.current?.(point);
      }
    });
    map.on('load', () => {
      setGeoJson(map, 'candidate-route', null, 'route');
      setGeoJson(map, 'source-shape', null, 'shape');
    });
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const apply = () => {
      setGeoJson(map, 'candidate-route', route ?? null, 'route');
      setGeoJson(map, 'source-shape', sourceShapeOnRoute(sourceShape, route), 'shape');
      if (route?.coordinates.length) {
        const bounds = new maplibregl.LngLatBounds();
        route.coordinates.forEach((point) => bounds.extend([point[0] ?? 0, point[1] ?? 0]));
        map.fitBounds(bounds, { padding: 48, maxZoom: 15, duration: 500 });
      }
    };
    if (map.isStyleLoaded()) apply();
    else map.once('load', apply);
  }, [route, sourceShape]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !start) return;
    if (!startMarkerRef.current) {
      const element = document.createElement('div');
      element.className = 'start-marker';
      element.setAttribute('aria-label', '출발점');
      startMarkerRef.current = new maplibregl.Marker({ element }).setLngLat([start.lng, start.lat]).addTo(map);
    } else {
      startMarkerRef.current.setLngLat([start.lng, start.lat]);
    }
    if (!route) map.easeTo({ center: [start.lng, start.lat], zoom: Math.max(map.getZoom(), 13) });
  }, [start, route]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    waypointMarkersRef.current.forEach((marker) => marker.remove());
    waypointMarkersRef.current = waypoints.map((point, index) => {
      const element = document.createElement('button');
      element.type = 'button';
      element.className = 'waypoint-marker';
      element.textContent = String(index + 1);
      element.setAttribute('aria-label', `${index + 1}번 경유점`);
      element.addEventListener('click', (event) => {
        event.stopPropagation();
        onWaypointSelect?.(index);
      });
      const marker = new maplibregl.Marker({ element, draggable: editable })
        .setLngLat([point[0] ?? 0, point[1] ?? 0])
        .addTo(map);
      if (editable) {
        marker.on('dragend', () => {
          const location = marker.getLngLat();
          onWaypointMove?.(index, [location.lng, location.lat]);
        });
      }
      return marker;
    });
    return () => waypointMarkersRef.current.forEach((marker) => marker.remove());
  }, [waypoints, editable, onWaypointMove, onWaypointSelect]);

  return <div ref={containerRef} className={`course-map ${className || ''}`} aria-label="코스 지도" />;
}
