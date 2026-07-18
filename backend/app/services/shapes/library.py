from __future__ import annotations

import itertools
import math
from collections.abc import Iterable

import numpy as np

from app.errors import AppError
from app.services.shapes.freehand import normalize_freehand

Point2D = tuple[float, float]


def _normalize(points: Iterable[Point2D], *, close: bool = True) -> list[Point2D]:
    array = np.asarray(list(points), dtype=float)
    if array.ndim != 2 or array.shape[0] < 2 or array.shape[1] != 2:
        raise ValueError("shape requires at least two 2D points")
    minimum = array.min(axis=0)
    maximum = array.max(axis=0)
    extent = maximum - minimum
    if np.any(extent <= 1e-12):
        raise ValueError("shape has zero width or height")
    scale = float(max(extent))
    normalized = (array - minimum) / scale
    offset = (1.0 - (extent / scale)) / 2.0
    normalized += offset
    result = [(float(x), float(y)) for x, y in normalized]
    if close and result[0] != result[-1]:
        result.append(result[0])
    return result


def heart(samples: int = 240) -> list[Point2D]:
    values: list[Point2D] = []
    for index in range(samples):
        t = 2 * math.pi * index / (samples - 1)
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        values.append((x, -y))
    return _normalize(values)


def star() -> list[Point2D]:
    values: list[Point2D] = []
    for index in range(10):
        angle = -math.pi / 2 + index * math.pi / 5
        radius = 1.0 if index % 2 == 0 else 0.42
        values.append((radius * math.cos(angle), radius * math.sin(angle)))
    values.append(values[0])
    return _normalize(values)


def circle(samples: int = 180) -> list[Point2D]:
    return _normalize(
        (math.cos(2 * math.pi * index / (samples - 1)), math.sin(2 * math.pi * index / (samples - 1)))
        for index in range(samples)
    )


def square() -> list[Point2D]:
    return [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]


def dog_face() -> list[Point2D]:
    """A single continuous stroke containing only a dog's face."""
    return _normalize(
        [
            (0.25, 0.20), (0.04, 0.04), (0.08, 0.45), (0.20, 0.55),
            (0.17, 0.75), (0.32, 0.94), (0.50, 1.00), (0.68, 0.94),
            (0.83, 0.75), (0.80, 0.55), (0.92, 0.45), (0.96, 0.04),
            (0.75, 0.20), (0.62, 0.13), (0.38, 0.13), (0.25, 0.20),
            (0.31, 0.43), (0.39, 0.40), (0.31, 0.43), (0.50, 0.58),
            (0.58, 0.66), (0.50, 0.75), (0.42, 0.66), (0.50, 0.58),
            (0.69, 0.43), (0.61, 0.40), (0.69, 0.43), (0.75, 0.20),
            (0.25, 0.20),
        ]
    )


def cat_face() -> list[Point2D]:
    """A single continuous stroke containing only a cat's face."""
    return _normalize(
        [
            (0.10, 0.34), (0.07, 0.02), (0.30, 0.17), (0.50, 0.10),
            (0.70, 0.17), (0.93, 0.02), (0.90, 0.34), (0.96, 0.55),
            (0.84, 0.79), (0.66, 0.96), (0.50, 1.00), (0.34, 0.96),
            (0.16, 0.79), (0.04, 0.55), (0.10, 0.34), (0.28, 0.42),
            (0.40, 0.46), (0.28, 0.42), (0.50, 0.60), (0.56, 0.66),
            (0.50, 0.72), (0.44, 0.66), (0.50, 0.60), (0.72, 0.42),
            (0.60, 0.46), (0.72, 0.42), (0.90, 0.34), (0.10, 0.34),
        ]
    )


LETTER_STROKES: dict[str, list[Point2D]] = {
    "A": [(0, 1), (0.5, 0), (1, 1), (0.75, 0.55), (0.25, 0.55), (0, 1)],
    "C": [(1, 0.15), (0.75, 0), (0.2, 0), (0, 0.25), (0, 0.75), (0.2, 1), (0.75, 1), (1, 0.85)],
    "H": [(0, 0), (0, 1), (0, 0.5), (1, 0.5), (1, 0), (1, 1)],
    "M": [(0, 1), (0, 0), (0.5, 0.55), (1, 0), (1, 1)],
    "R": [(0, 1), (0, 0), (0.7, 0), (1, 0.2), (0.7, 0.5), (0, 0.5), (1, 1)],
    "S": [(1, 0.1), (0.75, 0), (0.2, 0), (0, 0.2), (0.2, 0.5), (0.8, 0.5), (1, 0.8), (0.8, 1), (0.2, 1), (0, 0.9)],
    "U": [(0, 0), (0, 0.75), (0.2, 1), (0.8, 1), (1, 0.75), (1, 0)],
}


def letter(text: str) -> list[Point2D]:
    text = text.upper()
    unsupported = sorted(set(text) - LETTER_STROKES.keys())
    if unsupported:
        raise AppError(
            "VALIDATION_ERROR",
            "지원하지 않는 글자가 포함되어 있습니다.",
            422,
            {"supportedLetters": sorted(LETTER_STROKES), "unsupported": unsupported},
        )
    result: list[Point2D] = []
    spacing = 0.25
    for char_index, char in enumerate(text):
        x_offset = char_index * (1 + spacing)
        stroke = [(x + x_offset, y) for x, y in LETTER_STROKES[char]]
        if result:
            result.append(stroke[0])
        result.extend(stroke)
    return _normalize(result, close=True)


def polyline_length(points: list[Point2D]) -> float:
    return sum(math.dist(a, b) for a, b in itertools.pairwise(points))


def resample_by_length(points: list[Point2D], count: int, *, closed: bool = True) -> list[Point2D]:
    if count < 2:
        raise ValueError("count must be at least 2")
    source = list(points)
    if closed and source[0] != source[-1]:
        source.append(source[0])
    segment_lengths = np.asarray([math.dist(a, b) for a, b in itertools.pairwise(source)], dtype=float)
    total = float(segment_lengths.sum())
    if total <= 1e-12:
        raise ValueError("cannot resample zero-length shape")
    cumulative = np.concatenate(([0.0], np.cumsum(segment_lengths)))
    targets = np.linspace(0.0, total, count, endpoint=not closed)
    result: list[Point2D] = []
    for target in targets:
        index = int(np.searchsorted(cumulative, target, side="right") - 1)
        index = min(index, len(source) - 2)
        start_distance = cumulative[index]
        segment_length = segment_lengths[index]
        ratio = 0.0 if segment_length == 0 else float((target - start_distance) / segment_length)
        x = source[index][0] + (source[index + 1][0] - source[index][0]) * ratio
        y = source[index][1] + (source[index + 1][1] - source[index][1]) * ratio
        result.append((x, y))
    if closed:
        result.append(result[0])
    return result


def generate_shape(
    shape_type: str,
    *,
    shape_text: str | None = None,
    freehand_points: list[list[float]] | None = None,
    preview_count: int = 180,
) -> list[Point2D]:
    if shape_type == "heart":
        source = heart()
    elif shape_type == "star":
        source = star()
    elif shape_type == "circle":
        source = circle()
    elif shape_type == "square":
        source = square()
    elif shape_type == "dog":
        source = dog_face()
    elif shape_type == "cat":
        source = cat_face()
    elif shape_type == "letter":
        source = letter(shape_text or "")
    elif shape_type == "freehand":
        source = normalize_freehand(freehand_points or [], closed_loop=True)
    else:
        raise AppError("VALIDATION_ERROR", "지원하지 않는 도형입니다.", 422)
    return resample_by_length(source, preview_count, closed=True)
