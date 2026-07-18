import { useEffect, useMemo, useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useForm, useWatch } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';
import { aiApi, generationApi, geocodingApi } from '../api/endpoints';
import { FreehandCanvas } from '../components/FreehandCanvas';
import { ShapePreview } from '../components/ShapePreview';
import { inferRegion, isPointInRegion, regionOptions, regions } from '../config/regions';
import { CourseMap } from '../map/CourseMap';
import type { GeocodingResult, GenerationRequest, LngLat, ShapeType, SupportedRegion } from '../types/api';
import { errorMessage } from '../utils/error';

const supportedLetters = /^[ACHMRSU]{1,3}$/;
const schema = z
  .object({
    shapeType: z.enum(['heart', 'star', 'circle', 'square', 'dog', 'cat', 'letter', 'freehand']),
    shapeText: z.string().max(3),
    targetDistanceKm: z.coerce.number().min(1).max(30),
    distanceTolerancePct: z.coerce.number().min(5).max(25),
    rotationMode: z.enum(['auto', 'fixed']),
    rotationDeg: z.coerce.number().min(0).max(359),
    waypointCount: z.coerce.number().min(6).max(24),
    avoidMajorRoads: z.boolean(),
    preferFootways: z.boolean(),
    preferRiverside: z.boolean(),
    maxCandidates: z.coerce.number().min(1).max(5),
  })
  .superRefine((value, context) => {
    if (value.shapeType === 'letter' && !supportedLetters.test(value.shapeText.toUpperCase())) {
      context.addIssue({ code: 'custom', path: ['shapeText'], message: '지원 글자: A, C, H, M, R, S, U' });
    }
  });

type FormInput = z.input<typeof schema>;
type FormValues = z.output<typeof schema>;

const defaultFormValues: FormInput = {
  shapeType: 'heart',
  shapeText: 'A',
  targetDistanceKm: 5,
  distanceTolerancePct: 12,
  rotationMode: 'auto',
  rotationDeg: 0,
  waypointCount: 14,
  avoidMajorRoads: true,
  preferFootways: false,
  preferRiverside: false,
  maxCandidates: 3,
};

const builderDraftKey = 'runcanvas.builder-draft.v1';

interface BuilderDraft {
  region: SupportedRegion;
  start: LngLat;
  freehandPoints: number[][];
  address: string;
  naturalText: string;
  formValues: FormValues;
}

function readBuilderDraft(): BuilderDraft | null {
  if (typeof window === 'undefined') return null;
  try {
    const draft = JSON.parse(window.localStorage.getItem(builderDraftKey) || 'null') as Partial<BuilderDraft> | null;
    if (!draft || !draft.start || !Number.isFinite(draft.start.lat) || !Number.isFinite(draft.start.lng)) return null;
    const parsedForm = schema.safeParse(draft.formValues);
    if (!parsedForm.success) return null;
    return {
      region: draft.region === 'cheongju' || draft.region === 'seoul'
        ? draft.region
        : inferRegion(draft.start) ?? 'seoul',
      start: draft.start,
      freehandPoints: Array.isArray(draft.freehandPoints) ? draft.freehandPoints : [],
      address: typeof draft.address === 'string' ? draft.address : '',
      naturalText: typeof draft.naturalText === 'string' ? draft.naturalText : '',
      formValues: parsedForm.data,
    };
  } catch {
    return null;
  }
}

const shapes: { value: ShapeType; label: string }[] = [
  { value: 'heart', label: '하트' },
  { value: 'star', label: '별' },
  { value: 'circle', label: '원' },
  { value: 'square', label: '사각형' },
  { value: 'dog', label: '강아지' },
  { value: 'cat', label: '고양이' },
  { value: 'letter', label: '글자' },
  { value: 'freehand', label: '직접 그리기' },
];

export function BuilderPage() {
  const navigate = useNavigate();
  const [initialDraft] = useState(readBuilderDraft);
  const [region, setRegion] = useState<SupportedRegion>(initialDraft?.region ?? 'seoul');
  const [start, setStart] = useState<LngLat>(initialDraft?.start ?? regions.seoul.center);
  const [freehandPoints, setFreehandPoints] = useState<number[][]>(initialDraft?.freehandPoints ?? []);
  const [address, setAddress] = useState(initialDraft?.address ?? '');
  const [searchResults, setSearchResults] = useState<GeocodingResult[]>([]);
  const [naturalText, setNaturalText] = useState(initialDraft?.naturalText ?? '');
  const [locationError, setLocationError] = useState<string | null>(null);
  const form = useForm<FormInput, undefined, FormValues>({
    resolver: zodResolver(schema),
    defaultValues: initialDraft?.formValues ?? defaultFormValues,
  });
  const formValues = useWatch({ control: form.control });
  const shapeType = useWatch({ control: form.control, name: 'shapeType' });
  const shapeText = useWatch({ control: form.control, name: 'shapeText' });
  const rotationMode = useWatch({ control: form.control, name: 'rotationMode' });

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      try {
        window.localStorage.setItem(
          builderDraftKey,
          JSON.stringify({ region, start, freehandPoints, address, naturalText, formValues }),
        );
      } catch {
        // Storage may be unavailable in a private browser window; the form still works in memory.
      }
    }, 100);
    return () => window.clearTimeout(timeout);
  }, [address, formValues, freehandPoints, naturalText, region, start]);

  const geocode = useMutation({
    mutationFn: ({ query, selectedRegion }: { query: string; selectedRegion: SupportedRegion }) =>
      geocodingApi.search(query, selectedRegion),
    onSuccess: (data) => setSearchResults(data.items),
  });
  const parse = useMutation({
    mutationFn: aiApi.parse,
    onSuccess: (data) => {
      if (!data.result) return;
      form.setValue('shapeType', data.result.shapeType);
      form.setValue('targetDistanceKm', data.result.targetDistanceKm);
      form.setValue('avoidMajorRoads', data.result.avoidMajorRoads);
      form.setValue('preferFootways', data.result.preferFootways);
      form.setValue('preferRiverside', data.result.preferRiverside);
      if (data.result.locationText) setAddress(data.result.locationText);
    },
  });
  const create = useMutation({
    mutationFn: generationApi.create,
    onSuccess: (job) => navigate(`/jobs/${job.id}`),
  });

  const startLabel = useMemo(() => `${start.lat.toFixed(5)}, ${start.lng.toFixed(5)}`, [start]);

  const selectStart = (point: LngLat) => {
    if (!isPointInRegion(point, region)) {
      setLocationError(`${regions[region].label} 지원 범위 안에서 출발점을 선택해 주세요.`);
      return;
    }
    setLocationError(null);
    setStart(point);
  };

  const changeRegion = (nextRegion: SupportedRegion) => {
    setRegion(nextRegion);
    setStart(regions[nextRegion].center);
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
      (position) => {
        selectStart({ lng: position.coords.longitude, lat: position.coords.latitude });
      },
      () => setLocationError('위치 권한을 허용하거나 지도에서 출발점을 선택해 주세요.'),
      { enableHighAccuracy: true, timeout: 10_000, maximumAge: 30_000 },
    );
  };

  const submit = form.handleSubmit((values) => {
    const payload: GenerationRequest = {
      region,
      start,
      shapeType: values.shapeType,
      targetDistanceKm: values.targetDistanceKm,
      distanceTolerancePct: values.distanceTolerancePct,
      closedLoop: true,
      rotationMode: values.rotationMode,
      rotationDeg: values.rotationMode === 'fixed' ? values.rotationDeg : null,
      waypointCount: values.waypointCount,
      shapeText: values.shapeType === 'letter' ? values.shapeText.toUpperCase() : null,
      freehandPoints: values.shapeType === 'freehand' ? freehandPoints : null,
      preferences: {
        avoidMajorRoads: values.avoidMajorRoads,
        preferFootways: values.preferFootways,
        preferRiverside: values.preferRiverside,
      },
      maxCandidates: values.maxCandidates,
    };
    if (values.shapeType === 'freehand' && freehandPoints.length < 3) {
      form.setError('shapeType', { message: '캔버스에 그림을 그려 주세요.' });
      return;
    }
    create.mutate(payload);
  });

  return (
    <section>
      <div className="page-heading">
        <div>
          <span className="eyebrow">COURSE BUILDER</span>
          <h1>어떤 선을 달리고 싶나요?</h1>
          <p>지도에서 출발점을 고르고 그림과 거리를 설정하면 1~3개의 실제 보행 코스를 만듭니다.</p>
        </div>
      </div>

      <div className="builder-grid">
        <div className="builder-map-panel">
          <CourseMap center={regions[region].center} start={start} onMapClick={selectStart} />
          <div className="map-hint map-hint-actions">
            <span>지도를 클릭해 출발점을 이동하세요 · {startLabel}</span>
            <button type="button" className="button ghost compact" onClick={useCurrentLocation}>
              현재 위치 사용
            </button>
          </div>
          {locationError && <div className="alert warning">{locationError}</div>}
        </div>

        <form className="builder-form" onSubmit={submit}>
          <div className="form-section">
            <label htmlFor="region">도시 선택</label>
            <select
              id="region"
              value={region}
              onChange={(event) => changeRegion(event.target.value as SupportedRegion)}
            >
              {regionOptions.map((item) => (
                <option value={item.code} key={item.code}>{item.label}</option>
              ))}
            </select>
            <small>선택한 도시 안에서 주소와 출발점을 찾습니다.</small>
          </div>

          <div className="form-section natural-input">
            <label htmlFor="natural">한 문장으로 입력</label>
            <div className="inline-input">
              <input
                id="natural"
                value={naturalText}
                onChange={(event) => setNaturalText(event.target.value)}
                placeholder="잠실 근처에서 8km 하트, 큰길은 피해줘"
              />
              <button
                type="button"
                className="button secondary"
                disabled={parse.isPending || naturalText.length < 2}
                onClick={() => parse.mutate(naturalText)}
              >
                해석
              </button>
            </div>
            <small>규칙 파서가 우선하며 AI가 꺼져 있어도 아래 폼은 완전히 동작합니다.</small>
          </div>

          <div className="form-section">
            <label>주소 검색</label>
            <div className="inline-input">
              <input value={address} onChange={(event) => setAddress(event.target.value)} placeholder="잠실종합운동장" />
              <button
                type="button"
                className="button secondary"
                disabled={geocode.isPending || address.length < 2}
                onClick={() => geocode.mutate({ query: address, selectedRegion: region })}
              >
                검색
              </button>
            </div>
            {searchResults.length > 0 && (
              <div className="search-results">
                {searchResults.map((result) => (
                  <button
                    type="button"
                    key={`${result.lat}-${result.lng}`}
                    onClick={() => {
                      selectStart({ lat: result.lat, lng: result.lng });
                      setAddress(result.displayName);
                      setSearchResults([]);
                    }}
                  >
                    {result.displayName}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="form-section">
            <label>그림 선택</label>
            <div className="shape-selector">
              {shapes.map((shape) => (
                <button
                  type="button"
                  key={shape.value}
                  className={shapeType === shape.value ? 'active' : ''}
                  onClick={() => form.setValue('shapeType', shape.value)}
                >
                  <ShapePreview shape={shape.value === 'freehand' ? 'heart' : shape.value} letter={shapeText} />
                  <span>{shape.label}</span>
                </button>
              ))}
            </div>
            {form.formState.errors.shapeType && <small className="field-error">{form.formState.errors.shapeType.message}</small>}
          </div>

          {shapeType === 'letter' && (
            <label>
              영문자 1~3자
              <input {...form.register('shapeText')} maxLength={3} />
              {form.formState.errors.shapeText && <small className="field-error">{form.formState.errors.shapeText.message}</small>}
            </label>
          )}

          {shapeType === 'freehand' && <FreehandCanvas value={freehandPoints} onChange={setFreehandPoints} />}

          <div className="two-columns">
            <label>
              목표 거리 (km)
              <input type="number" step="0.5" {...form.register('targetDistanceKm')} />
              {form.formState.errors.targetDistanceKm && <small className="field-error">{form.formState.errors.targetDistanceKm.message}</small>}
            </label>
            <label>
              허용 오차 (%)
              <input type="number" {...form.register('distanceTolerancePct')} />
            </label>
          </div>

          <div className="two-columns">
            <label>
              회전
              <select {...form.register('rotationMode')}>
                <option value="auto">자동 탐색</option>
                <option value="fixed">각도 고정</option>
              </select>
            </label>
            {rotationMode === 'fixed' && (
              <label>
                각도
                <input type="number" {...form.register('rotationDeg')} />
              </label>
            )}
          </div>

          <details className="advanced-settings">
            <summary>고급 설정</summary>
            <div className="two-columns">
              <label>
                경유점 수
                <input type="number" {...form.register('waypointCount')} />
              </label>
              <label>
                최대 후보
                <select {...form.register('maxCandidates')}>
                  <option value="1">1개</option>
                  <option value="2">2개</option>
                  <option value="3">3개</option>
                  <option value="4">4개</option>
                  <option value="5">5개</option>
                </select>
              </label>
            </div>
            <label className="check-row">
              <input type="checkbox" {...form.register('avoidMajorRoads')} />
              큰 도로 회피
            </label>
            <label className="check-row">
              <input type="checkbox" {...form.register('preferFootways')} />
              보행로 선호
            </label>
            <label className="check-row">
              <input type="checkbox" {...form.register('preferRiverside')} />
              강변 경로 강하게 선호
            </label>
          </details>

          {(create.isError || geocode.isError || parse.isError) && (
            <div className="alert error">{errorMessage(create.error || geocode.error || parse.error)}</div>
          )}
          <button className="button primary wide large-button" disabled={create.isPending}>
            {create.isPending ? '작업을 만드는 중…' : 'GPS 아트 코스 생성'}
          </button>
        </form>
      </div>
    </section>
  );
}
