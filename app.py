import streamlit as st
from color_models import (
	rgb255_to_xyz100,
	xyz100_to_rgb255,
	rgb255_to_hsv_deg,
	hsv_deg_to_rgb255,
	xyz100_to_hsv_deg,
	hsv_deg_to_xyz100,
	rgb_to_hex,
	hex_to_rgb,
)

st.set_page_config(page_title="RGB ↔ XYZ ↔ HSV", layout="wide")


def _set_source_rgb():
	st.session_state.source_model = "rgb"


def _set_source_hsv():
	st.session_state.source_model = "hsv"


def _set_source_xyz():
	st.session_state.source_model = "xyz"


def _on_hex_change():
	st.session_state.source_model = "rgb"
	r, g, b = hex_to_rgb(st.session_state.hex)
	st.session_state.r = r
	st.session_state.g = g
	st.session_state.b = b


def _number_input_callback_factory(target_key, after_change):
	number_key = f"{target_key}_number"

	def _callback():
		st.session_state[target_key] = st.session_state[number_key]
		if after_change:
			after_change()

	return _callback


def _slider_with_number(label, min_value, max_value, key, on_change, step=None, number_format=None):
	is_float = isinstance(min_value, float) or isinstance(max_value, float)
	step_value = step if step is not None else (0.001 if is_float else 1)
	format_value = number_format if number_format else ("%.3f" if is_float else None)
	number_key = f"{key}_number"
	if key in st.session_state:
		st.session_state[number_key] = st.session_state.get(number_key, st.session_state[key])
		st.session_state[number_key] = st.session_state[key]
	else:
		st.session_state[key] = min_value
		st.session_state[number_key] = min_value
	slider_col, input_col = st.columns([4, 1])
	with slider_col:
		st.slider(label, min_value, max_value, key=key, on_change=on_change)
	with input_col:
		st.number_input(
			label,
			min_value=min_value,
			max_value=max_value,
			step=step_value,
			key=number_key,
			format=format_value,
			label_visibility="collapsed",
			on_change=_number_input_callback_factory(key, on_change),
		)


def _clamp_round(value: float, min_value: float, max_value: float) -> float:
	clamped = min(max(float(value), min_value), max_value)
	return round(clamped, 3)


if "initialized" not in st.session_state:
	st.session_state.r = 255
	st.session_state.g = 0
	st.session_state.b = 0
	h, s, v = rgb255_to_hsv_deg(255, 0, 0)
	X, Y, Z = rgb255_to_xyz100(255, 0, 0)
	st.session_state.h = int(round(h))
	st.session_state.s = int(round(s))
	st.session_state.v = int(round(v))
	st.session_state.X = _clamp_round(X, 0.0, 95.047)
	st.session_state.Y = _clamp_round(Y, 0.0, 100.0)
	st.session_state.Z = _clamp_round(Z, 0.0, 108.883)
	st.session_state.hex = rgb_to_hex(255, 0, 0)
	st.session_state.source_model = "rgb"
	st.session_state.clip_warning = False
	st.session_state.initialized = True

st.session_state.X = _clamp_round(st.session_state.get("X", 0.0), 0.0, 95.047)
st.session_state.Y = _clamp_round(st.session_state.get("Y", 0.0), 0.0, 100.0)
st.session_state.Z = _clamp_round(st.session_state.get("Z", 0.0), 0.0, 108.883)

clip_warning = False
source = st.session_state.get("source_model", "rgb")
if source == "rgb":
	r, g, b = int(st.session_state.r), int(st.session_state.g), int(st.session_state.b)
	h, s, v = rgb255_to_hsv_deg(r, g, b)
	X, Y, Z = rgb255_to_xyz100(r, g, b)
	st.session_state.h = int(round(h))
	st.session_state.s = int(round(s))
	st.session_state.v = int(round(v))
	st.session_state.X = _clamp_round(X, 0.0, 95.047)
	st.session_state.Y = _clamp_round(Y, 0.0, 100.0)
	st.session_state.Z = _clamp_round(Z, 0.0, 108.883)
	st.session_state.hex = rgb_to_hex(r, g, b)
elif source == "hsv":
	h = float(st.session_state.h)
	s = float(st.session_state.s)
	v = float(st.session_state.v)
	r, g, b = hsv_deg_to_rgb255(h, s, v)
	X, Y, Z = rgb255_to_xyz100(r, g, b)
	st.session_state.r = int(r)
	st.session_state.g = int(g)
	st.session_state.b = int(b)
	st.session_state.X = _clamp_round(X, 0.0, 95.047)
	st.session_state.Y = _clamp_round(Y, 0.0, 100.0)
	st.session_state.Z = _clamp_round(Z, 0.0, 108.883)
	st.session_state.hex = rgb_to_hex(r, g, b)
else:  # xyz
	X = float(st.session_state.X)
	Y = float(st.session_state.Y)
	Z = float(st.session_state.Z)
	(rgb, clipped) = xyz100_to_rgb255(X, Y, Z)
	r, g, b = rgb
	(hsv, hsv_clipped) = xyz100_to_hsv_deg(X, Y, Z)
	h, s, v = hsv
	st.session_state.r = int(r)
	st.session_state.g = int(g)
	st.session_state.b = int(b)
	st.session_state.h = int(round(h))
	st.session_state.s = int(round(s))
	st.session_state.v = int(round(v))
	st.session_state.hex = rgb_to_hex(r, g, b)
	clip_warning = bool(clipped or hsv_clipped)

st.title("Цветовые модели: RGB ↔ XYZ ↔ HSV")
st.caption("Интерактивная синхронизация трёх моделей. XYZ (D65): X≤95.047, Y≤100, Z≤108.883. HSV — H:0–360°, S/V:0–100%.")

st.color_picker("Палитра (sRGB)", key="hex", on_change=_on_hex_change)

col1, col2, col3 = st.columns(3)

with col1:
	st.subheader("RGB")
	_slider_with_number("R", 0, 255, key="r", on_change=_set_source_rgb)
	_slider_with_number("G", 0, 255, key="g", on_change=_set_source_rgb)
	_slider_with_number("B", 0, 255, key="b", on_change=_set_source_rgb)

with col2:
	st.subheader("HSV")
	_slider_with_number("H (°)", 0, 360, key="h", on_change=_set_source_hsv)
	_slider_with_number("S (%)", 0, 100, key="s", on_change=_set_source_hsv)
	_slider_with_number("V (%)", 0, 100, key="v", on_change=_set_source_hsv)

with col3:
	st.subheader("XYZ (D65)")
	_slider_with_number("X", 0.0, 95.047, key="X", on_change=_set_source_xyz, step=0.001)
	_slider_with_number("Y", 0.0, 100.0, key="Y", on_change=_set_source_xyz, step=0.001)
	_slider_with_number("Z", 0.0, 108.883, key="Z", on_change=_set_source_xyz, step=0.001)

# Preview large swatch
st.markdown("---")
st.write("Предпросмотр")
preview_col = st.columns([1, 3, 1])[1]
with preview_col:
	st.markdown(
		f"""
		<div style='width:100%;height:160px;border-radius:8px;border:1px solid #ddd;background:{st.session_state.hex};'></div>
		""",
		unsafe_allow_html=True,
	)
