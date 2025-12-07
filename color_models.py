from __future__ import annotations

from dataclasses import dataclass
import colorsys
from typing import Tuple


# sRGB <-> XYZ (D65) matrices from IEC 61966-2-1:1999
_SRGB_TO_XYZ = (
	(0.4124564, 0.3575761, 0.1804375),
	(0.2126729, 0.7151522, 0.0721750),
	(0.0193339, 0.1191920, 0.9503041),
)

_XYZ_TO_SRGB = (
	(3.2404542, -1.5371385, -0.4985314),
	(-0.9692660, 1.8760108, 0.0415560),
	(0.0556434, -0.2040259, 1.0572252),
)


def _clamp(value: float, min_value: float, max_value: float) -> float:
	if value < min_value:
		return min_value
	if value > max_value:
		return max_value
	return value


def _srgb_to_linear(c: float) -> float:
	# c in [0,1]
	if c <= 0.04045:
		return c / 12.92
	return ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c: float) -> float:
	# c in [0,1]
	if c <= 0.0031308:
		return 12.92 * c
	return 1.055 * (c ** (1.0 / 2.4)) - 0.055


def _dot3(m: Tuple[Tuple[float, float, float], ...], v: Tuple[float, float, float]) -> Tuple[float, float, float]:
	a = m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2]
	b = m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2]
	c = m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2]
	return (a, b, c)


def rgb255_to_xyz100(r: int, g: int, b: int) -> Tuple[float, float, float]:
	"""Convert 8-bit sRGB to CIE XYZ scaled to 0..100 (D65)."""
	r = _clamp(r, 0, 255)
	g = _clamp(g, 0, 255)
	b = _clamp(b, 0, 255)
	# Normalize to 0..1
	r_s = r / 255.0
	g_s = g / 255.0
	b_s = b / 255.0
	# Remove gamma
	r_lin = _srgb_to_linear(r_s)
	g_lin = _srgb_to_linear(g_s)
	b_lin = _srgb_to_linear(b_s)
	X, Y, Z = _dot3(_SRGB_TO_XYZ, (r_lin, g_lin, b_lin))
	# Scale to 0..100 for UI familiarity
	return (X * 100.0, Y * 100.0, Z * 100.0)


def xyz100_to_rgb255(X: float, Y: float, Z: float) -> Tuple[Tuple[int, int, int], bool]:
	"""Convert XYZ (0..100, D65) to 8-bit sRGB. Returns (rgb, clipped)."""
	# Unscale from 0..100
	Xn = X / 100.0
	Yn = Y / 100.0
	Zn = Z / 100.0
	# Linear RGB (can be out of gamut)
	r_lin, g_lin, b_lin = _dot3(_XYZ_TO_SRGB, (Xn, Yn, Zn))
	# Track clipping before gamma
	clipped = False
	if not (0.0 <= r_lin <= 1.0) or not (0.0 <= g_lin <= 1.0) or not (0.0 <= b_lin <= 1.0):
		clipped = True
	# Apply gamma and clamp to 0..1
	r_srgb = _linear_to_srgb(_clamp(r_lin, 0.0, 1.0))
	g_srgb = _linear_to_srgb(_clamp(g_lin, 0.0, 1.0))
	b_srgb = _linear_to_srgb(_clamp(b_lin, 0.0, 1.0))
	# Convert to 0..255
	r8 = int(round(_clamp(r_srgb, 0.0, 1.0) * 255.0))
	g8 = int(round(_clamp(g_srgb, 0.0, 1.0) * 255.0))
	b8 = int(round(_clamp(b_srgb, 0.0, 1.0) * 255.0))
	# Extra check if rounding pushes to 256 or negative
	r8 = max(0, min(255, r8))
	g8 = max(0, min(255, g8))
	b8 = max(0, min(255, b8))
	return (r8, g8, b8), clipped


def rgb255_to_hsv_deg(r: int, g: int, b: int) -> Tuple[float, float, float]:
	"""Convert 8-bit sRGB to HSV with H in degrees [0..360), S,V in percent [0..100]."""
	r_s = _clamp(r, 0, 255) / 255.0
	g_s = _clamp(g, 0, 255) / 255.0
	b_s = _clamp(b, 0, 255) / 255.0
	h, s, v = colorsys.rgb_to_hsv(r_s, g_s, b_s)  # h,s,v in 0..1
	return (h * 360.0, s * 100.0, v * 100.0)


def hsv_deg_to_rgb255(h_deg: float, s_perc: float, v_perc: float) -> Tuple[int, int, int]:
	"""Convert HSV with degrees/percent to 8-bit sRGB."""
	h = (h_deg % 360.0) / 360.0
	s = _clamp(s_perc, 0.0, 100.0) / 100.0
	v = _clamp(v_perc, 0.0, 100.0) / 100.0
	r_s, g_s, b_s = colorsys.hsv_to_rgb(h, s, v)
	r8 = int(round(_clamp(r_s, 0.0, 1.0) * 255.0))
	g8 = int(round(_clamp(g_s, 0.0, 1.0) * 255.0))
	b8 = int(round(_clamp(b_s, 0.0, 1.0) * 255.0))
	return max(0, min(255, r8)), max(0, min(255, g8)), max(0, min(255, b8))


def xyz100_to_hsv_deg(X: float, Y: float, Z: float) -> Tuple[Tuple[float, float, float], bool]:
	"""XYZ (0..100) -> HSV (deg, %) via sRGB. Returns (hsv, clipped)."""
	(rgb, clipped) = xyz100_to_rgb255(X, Y, Z)
	h, s, v = rgb255_to_hsv_deg(*rgb)
	return (h, s, v), clipped


def hsv_deg_to_xyz100(h_deg: float, s_perc: float, v_perc: float) -> Tuple[float, float, float]:
	"""HSV (deg, %) -> XYZ (0..100) via sRGB."""
	r, g, b = hsv_deg_to_rgb255(h_deg, s_perc, v_perc)
	return rgb255_to_xyz100(r, g, b)


def rgb_to_hex(r: int, g: int, b: int) -> str:
	return f"#{r:02X}{g:02X}{b:02X}"


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
	hs = hex_str.strip().lstrip('#')
	if len(hs) != 6:
		return (0, 0, 0)
	r = int(hs[0:2], 16)
	g = int(hs[2:4], 16)
	b = int(hs[4:6], 16)
	return (r, g, b)
