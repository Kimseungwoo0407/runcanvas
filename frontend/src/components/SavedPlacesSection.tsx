import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { geocodingApi, savedPlaceApi } from '../api/endpoints';
import { isPointInRegion, regionOptions, regions } from '../config/regions';
import { CourseMap } from '../map/CourseMap';
import type { GeocodingResult, LngLat, PrecomputeShape, SavedPlaceCreateRequest, SupportedRegion } from '../types/api';
import { errorMessage } from '../utils/error';

const distanceOptions = [3, 5, 7, 10];
const shapeOptions: { value: PrecomputeShape; label: string }[] = [
  { value: 'circle', label: '원' },
  { value: 'heart', label: '하트' },
  { value: 'star', label: '별' },
  { value: 'square', label: '사각형' },
  { value: 'dog', label: '강아지 얼굴' },
  { value: 'cat', label: '고양이 얼굴' },
];

function progressLabel(status: { queued: number; running: number; succeeded: number; failed: number }) {
  if (status.running) return `${status.running}개 생성 중 · ${status.queued}개 대기`;
  if (status.queued) return `${status.queued}개 생성 대기 중`;
  if (status.failed) return `${status.succeeded}개 완료 · ${status.failed}개 실패`;
  return `${status.succeeded}개 준비 완료`;
}

export function SavedPlacesSection() {
  const queryClient = useQueryClient();
  const [region, setRegion] = useState<SupportedRegion>('seoul');
  const [name, setName] = useState('집 근처');
  const [address, setAddress] = useState('');
  const [location, setLocation] = useState<LngLat | null>(null);
  const [searchResults, setSearchResults] = useState<GeocodingResult[]>([]);
  const [privacyRadiusM, setPrivacyRadiusM] = useState(250);
  const [preferRiverside, setPreferRiverside] = useState(false);
  const [distancesKm, setDistancesKm] = useState<number[]>(distanceOptions);
  const [shapes, setShapes] = useState<PrecomputeShape[]>(['circle', 'heart', 'star']);
  const [locationError, setLocationError] = useState<string | null>(null);

  const places = useQuery({
    queryKey: ['saved-places'],
    queryFn: savedPlaceApi.list,
    refetchInterval: 5000,
  });
  const geocode = useMutation({
    mutationFn: ({ query, selectedRegion }: { query: string; selectedRegion: SupportedRegion }) =>
      geocodingApi.search(query, selectedRegion),
    onSuccess: (data) => setSearchResults(data.items),
  });
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['saved-places'] });
    queryClient.invalidateQueries({ queryKey: ['courses'] });
  };
  const create = useMutation({
    mutationFn: savedPlaceApi.create,
    onSuccess: refresh,
  });
  const regenerate = useMutation({
    mutationFn: savedPlaceApi.precompute,
    onSuccess: refresh,
  });
  const remove = useMutation({
    mutationFn: savedPlaceApi.remove,
    onSuccess: refresh,
  });

  const toggleDistance = (value: number) => {
    setDistancesKm((current) =>
      current.includes(value) ? current.filter((item) => item !== value) : [...current, value].sort((a, b) => a - b),
    );
  };
  const toggleShape = (value: PrecomputeShape) => {
    setShapes((current) =>
      current.includes(value) ? current.filter((item) => item !== value) : [...current, value],
    );
  };
  const selectLocation = (point: LngLat) => {
    if (!isPointInRegion(point, region)) {
      setLocationError(`${regions[region].label} 지원 범위 안에서 위치를 선택해 주세요.`);
      return;
    }
    setLocationError(null);
    setLocation(point);
  };
  const changeRegion = (nextRegion: SupportedRegion) => {
    setRegion(nextRegion);
    setLocation(null);
    setAddress('');
    setSearchResults([]);
    setLocationError(null);
  };
  const useCurrentLocation = () => {
    setLocationError(null);
    if (!navigator.geolocation) {
      setLocationError('이 브라우저는 현재 위치를 지원하지 않습니다.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => selectLocation({ lng: position.coords.longitude, lat: position.coords.latitude }),
      () => setLocationError('위치 권한을 허용하거나 지도에서 위치를 선택해 주세요.'),
      { enableHighAccuracy: true, timeout: 10_000, maximumAge: 30_000 },
    );
  };
  const submit = () => {
    if (!location || distancesKm.length === 0 || shapes.length === 0) return;
    const payload: SavedPlaceCreateRequest = {
      name,
      location,
      privacyRadiusM,
      preferRiverside,
      distancesKm,
      shapes,
    };
    create.mutate(payload);
  };

  return (
    <section className="saved-places-section">
      <div className="section-heading">
        <div>
          <span className="eyebrow">PRE-GENERATED ROUTES</span>
          <h2>자주 뛰는 장소</h2>
          <p>위치를 한 번 등록하면 선택한 거리와 모양의 코스를 백그라운드에서 미리 준비합니다.</p>
        </div>
      </div>

      {places.data?.items.length ? (
        <div className="saved-place-list">
          {places.data.items.map((place) => {
            const finished = place.status.succeeded + place.status.failed + place.status.cancelled;
            const progress = place.status.total ? Math.round((finished / place.status.total) * 100) : 0;
            return (
              <article className="saved-place-item" key={place.id}>
                <div>
                  <div className="saved-place-title">
                    <strong>{place.name}</strong>
                    {place.preferRiverside && <span className="river-badge">강변 선호</span>}
                  </div>
                  <small>
                    {place.distancesKm.join(' · ')}km · {place.shapes.map((shape) => shapeOptions.find((item) => item.value === shape)?.label).join(' · ')}
                  </small>
                  <div className="mini-progress"><div style={{ width: `${progress}%` }} /></div>
                  <span>{progressLabel(place.status)} · 저장 코스 {place.status.generatedCourses}개</span>
                </div>
                <div className="button-row">
                  <button
                    type="button"
                    className="button secondary compact"
                    disabled={regenerate.isPending}
                    onClick={() => regenerate.mutate(place.id)}
                  >
                    다시 만들기
                  </button>
                  <button
                    type="button"
                    className="button danger compact"
                    disabled={remove.isPending}
                    onClick={() => {
                      if (window.confirm(`'${place.name}' 장소를 삭제할까요? 만들어진 코스는 유지됩니다.`)) {
                        remove.mutate(place.id);
                      }
                    }}
                  >
                    삭제
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      ) : null}

      <div className="saved-place-editor">
        <div className="saved-place-map-wrap">
          <CourseMap
            center={regions[region].center}
            start={location}
            onMapClick={selectLocation}
            className="saved-place-map"
          />
          <div className="map-hint map-hint-actions">
            <span>{location ? `${location.lat.toFixed(5)}, ${location.lng.toFixed(5)}` : '지도를 클릭해 위치를 정하세요.'}</span>
            <button type="button" className="button ghost compact" onClick={useCurrentLocation}>현재 위치</button>
          </div>
        </div>
        <form
          className="saved-place-form"
          onSubmit={(event) => {
            event.preventDefault();
            submit();
          }}
        >
          <label>
            도시
            <select value={region} onChange={(event) => changeRegion(event.target.value as SupportedRegion)}>
              {regionOptions.map((item) => (
                <option value={item.code} key={item.code}>{item.label}</option>
              ))}
            </select>
          </label>
          <label>
            장소 이름
            <input value={name} maxLength={80} onChange={(event) => setName(event.target.value)} />
          </label>
          <label>주소 검색</label>
          <div className="inline-input">
            <input value={address} onChange={(event) => setAddress(event.target.value)} placeholder="집 근처 공원 또는 지하철역" />
            <button
              type="button"
              className="button secondary"
              disabled={geocode.isPending || address.length < 2}
              onClick={() => geocode.mutate({ query: address, selectedRegion: region })}
            >검색</button>
          </div>
          {searchResults.length > 0 && (
            <div className="search-results">
              {searchResults.map((result) => (
                <button
                  type="button"
                  key={`${result.lat}-${result.lng}`}
                  onClick={() => {
                    selectLocation({ lat: result.lat, lng: result.lng });
                    setAddress(result.displayName);
                    setSearchResults([]);
                  }}
                >
                  {result.displayName}
                </button>
              ))}
            </div>
          )}
          <label>
            집 좌표 이격 거리
            <select value={privacyRadiusM} onChange={(event) => setPrivacyRadiusM(Number(event.target.value))}>
              <option value={0}>이격 없음</option>
              <option value={150}>150m</option>
              <option value={250}>250m 권장</option>
              <option value={400}>400m</option>
            </select>
            <small>정확한 집 위치가 코스 시작점에 드러나지 않도록 출발점을 이동합니다.</small>
          </label>
          <fieldset>
            <legend>미리 만들 거리</legend>
            <div className="option-grid">
              {distanceOptions.map((value) => (
                <label className="option-chip" key={value}>
                  <input type="checkbox" checked={distancesKm.includes(value)} onChange={() => toggleDistance(value)} />
                  {value}km
                </label>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend>도형</legend>
            <div className="option-grid">
              {shapeOptions.map((shape) => (
                <label className="option-chip" key={shape.value}>
                  <input type="checkbox" checked={shapes.includes(shape.value)} onChange={() => toggleShape(shape.value)} />
                  {shape.label}
                </label>
              ))}
            </div>
          </fieldset>
          <label className="check-row river-option">
            <input type="checkbox" checked={preferRiverside} onChange={(event) => setPreferRiverside(event.target.checked)} />
            <span><strong>강변 경로 강하게 선호</strong><small>서울 한강과 청주 무심천 주변 보행로를 우선합니다.</small></span>
          </label>
          {locationError && <div className="alert warning">{locationError}</div>}
          {(create.isError || geocode.isError || regenerate.isError || remove.isError) && (
            <div className="alert error">{errorMessage(create.error || geocode.error || regenerate.error || remove.error)}</div>
          )}
          <button className="button primary" disabled={create.isPending || !location || !name.trim() || !distancesKm.length || !shapes.length}>
            {create.isPending ? '등록하는 중…' : `${distancesKm.length * shapes.length}개 코스 미리 만들기`}
          </button>
        </form>
      </div>
    </section>
  );
}
