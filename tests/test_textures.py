from __future__ import annotations

import pygame
import pytest

from orbit_sim.planet_textures import PlanetTextureLibrary


@pytest.fixture(scope="module")
def display():
    pygame.display.init()
    pygame.display.set_mode((16, 16))
    yield
    pygame.display.quit()


def test_has_texture_only_for_bodies_with_a_file(display):
    library = PlanetTextureLibrary()
    assert library.has_texture("Earth")
    assert library.has_texture("Neptune")
    assert not library.has_texture("Pluto")


def test_map_texture_is_scaled_to_a_two_to_one_equirectangular_size(display):
    texture = PlanetTextureLibrary().map_texture("Mars", 512)
    assert texture.get_size() == (512, 256)


def test_map_texture_enforces_a_minimum_width(display):
    texture = PlanetTextureLibrary().map_texture("Mars", 10)
    assert texture.get_size() == (256, 128)


def test_map_texture_is_cached_per_width(display):
    library = PlanetTextureLibrary()
    assert library.map_texture("Venus", 256) is library.map_texture("Venus", 256)
    assert library.map_texture("Venus", 256) is not library.map_texture("Venus", 512)


def test_missing_texture_returns_none(display):
    assert PlanetTextureLibrary().map_texture("Pluto", 256) is None


def test_auxiliary_texture_loads_the_ring_mask_with_alpha(display):
    ring = PlanetTextureLibrary().auxiliary_texture("saturn_ring_alpha", (256, 64))
    assert ring.get_size() == (256, 64)
    assert ring.get_flags() & pygame.SRCALPHA
    alphas = {ring.get_at((x, 32)).a for x in range(0, 256, 4)}
    # A real ring mask has both transparent gaps and opaque bands, not a flat fill.
    assert min(alphas) < 128 < max(alphas)


def test_luminance_rows_match_the_scaled_texture(display):
    rows = PlanetTextureLibrary().map_luminance("Mercury", 256)
    assert len(rows) == 128
    assert all(len(row) == 256 for row in rows)
