from __future__ import annotations

import itertools
import math

import pytest

from app.errors import AppError
from app.services.shapes.freehand import normalize_freehand
from app.services.shapes.library import generate_shape, resample_by_length


@pytest.mark.parametrize("shape", ["heart", "star", "circle", "square", "dog", "cat"])
def test_shapes_are_finite_closed_and_normalized(shape: str) -> None:
    points = generate_shape(shape, preview_count=64)
    assert len(points) == 65
    assert points[0] == points[-1]
    assert all(0 <= value <= 1 and math.isfinite(value) for point in points for value in point)


def test_resampling_has_nearly_equal_segments() -> None:
    points = generate_shape("circle", preview_count=48)
    sampled = resample_by_length(points, 24, closed=True)
    lengths = [math.dist(a, b) for a, b in itertools.pairwise(sampled)]
    assert max(lengths) / min(lengths) < 1.08


def test_letter_contract() -> None:
    points = generate_shape("letter", shape_text="A", preview_count=60)
    assert len(points) == 61
    assert points[0] == points[-1]


def test_unsupported_letter_is_rejected() -> None:
    with pytest.raises(AppError):
        generate_shape("letter", shape_text="Z")


def test_freehand_is_normalized_and_closed() -> None:
    points = normalize_freehand([[10, 10], [100, 10], [100, 80], [10, 80]], closed_loop=True)
    assert points[0] == points[-1]
    assert all(0 <= value <= 1 for point in points for value in point)


def test_freehand_rejects_extreme_aspect_ratio() -> None:
    with pytest.raises(AppError):
        normalize_freehand([[0, 0], [1000, 1], [500, 2]], closed_loop=True)
