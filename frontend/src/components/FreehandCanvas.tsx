import { useRef, useState } from 'react';

interface Props {
  value: number[][];
  onChange: (points: number[][]) => void;
}

export function FreehandCanvas({ value, onChange }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [drawing, setDrawing] = useState(false);

  const pointFromEvent = (event: React.PointerEvent<SVGSVGElement>) => {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return null;
    return [
      ((event.clientX - rect.left) / rect.width) * 320,
      ((event.clientY - rect.top) / rect.height) * 220,
    ];
  };

  const start = (event: React.PointerEvent<SVGSVGElement>) => {
    event.currentTarget.setPointerCapture(event.pointerId);
    const point = pointFromEvent(event);
    if (!point) return;
    setDrawing(true);
    onChange([point]);
  };

  const move = (event: React.PointerEvent<SVGSVGElement>) => {
    if (!drawing) return;
    const point = pointFromEvent(event);
    if (!point) return;
    const previous = value.at(-1);
    if (!previous || Math.hypot(point[0]! - previous[0]!, point[1]! - previous[1]!) > 3) {
      onChange([...value, point]);
    }
  };

  const path = value.map((point, index) => `${index ? 'L' : 'M'} ${point[0]} ${point[1]}`).join(' ');

  return (
    <div className="freehand-wrap">
      <svg
        ref={svgRef}
        viewBox="0 0 320 220"
        className="freehand-canvas"
        onPointerDown={start}
        onPointerMove={move}
        onPointerUp={() => setDrawing(false)}
        onPointerCancel={() => setDrawing(false)}
        aria-label="자유 드로잉 캔버스"
      >
        <path d={path} fill="none" stroke="currentColor" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <button type="button" className="button ghost" onClick={() => onChange([])}>
        다시 그리기
      </button>
    </div>
  );
}
