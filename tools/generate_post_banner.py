#!/usr/bin/env python3

import argparse
import math
import random
import struct
import zlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WIDTH = 1500
DEFAULT_HEIGHT = 380
DEFAULT_BG = "#D3D5D8"
DEFAULT_INK = "#000000"


def parse_color(value):
    value = value.strip()
    if value.startswith("#"):
        value = value[1:]

    if len(value) != 6:
        raise argparse.ArgumentTypeError("colors must use 6-digit hex, e.g. #D3D5D8")

    try:
        return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid hex color: {value}") from exc


class Canvas:
    def __init__(self, width, height, background, ink):
        self.width = width
        self.height = height
        self.background = background
        self.ink = ink
        self.pixels = bytearray(background) * (width * height)

    def set_pixel(self, x, y, color):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return

        index = (y * self.width + x) * 3
        self.pixels[index] = color[0]
        self.pixels[index + 1] = color[1]
        self.pixels[index + 2] = color[2]

    def fill_rect(self, x0, y0, x1, y1, color):
        x0 = max(0, int(x0))
        y0 = max(0, int(y0))
        x1 = min(self.width, int(x1))
        y1 = min(self.height, int(y1))

        for y in range(y0, y1):
            row = (y * self.width) * 3
            for x in range(x0, x1):
                index = row + x * 3
                self.pixels[index] = color[0]
                self.pixels[index + 1] = color[1]
                self.pixels[index + 2] = color[2]

    def fill_circle(self, cx, cy, radius, color):
        radius = int(radius)
        radius_squared = radius * radius
        x0 = max(0, int(cx - radius))
        x1 = min(self.width - 1, int(cx + radius))
        y0 = max(0, int(cy - radius))
        y1 = min(self.height - 1, int(cy + radius))

        for y in range(y0, y1 + 1):
            dy = y - cy
            for x in range(x0, x1 + 1):
                dx = x - cx
                if dx * dx + dy * dy <= radius_squared:
                    self.set_pixel(x, y, color)

    def draw_line(self, x0, y0, x1, y1, thickness, color):
        distance = max(abs(x1 - x0), abs(y1 - y0))
        if distance == 0:
            self.fill_circle(x0, y0, max(1, thickness // 2), color)
            return

        for step in range(distance + 1):
            t = step / distance
            x = round(x0 + (x1 - x0) * t)
            y = round(y0 + (y1 - y0) * t)
            self.fill_circle(x, y, max(1, thickness // 2), color)

    def fill_bottom_wave(self, top_function, color):
        for x in range(self.width):
            top_y = max(0, min(self.height, int(top_function(x))))
            for y in range(top_y, self.height):
                self.set_pixel(x, y, color)

    def dotted_band(self, top_function, bottom_function, spacing, dot_radius, color):
        for x in range(0, self.width, spacing):
            top_y = int(top_function(x))
            bottom_y = int(bottom_function(x))
            if bottom_y <= top_y:
                continue

            for y in range(top_y, bottom_y, spacing):
                self.fill_circle(x, y, dot_radius, color)

    def dotted_disc(self, cx, cy, radius, spacing, dot_radius, color):
        radius_squared = radius * radius
        for y in range(int(cy - radius), int(cy + radius) + 1, spacing):
            for x in range(int(cx - radius), int(cx + radius) + 1, spacing):
                dx = x - cx
                dy = y - cy
                if dx * dx + dy * dy <= radius_squared:
                    self.fill_circle(x, y, dot_radius, color)

    def striped_card(self, x, y, width, height, rows=3):
        self.fill_rect(x, y, x + width, y + height, self.ink)

        for py in range(y, y + height):
            for px in range(x, x + width):
                if ((px - x) + (py - y)) % 28 < 9:
                    self.set_pixel(px, py, self.background)

        self.fill_rect(x + 8, y + 8, x + width - 8, y + height - 8, self.ink)

        checkbox_x = x + 26
        line_x = x + 66
        row_y = y + 24
        row_gap = max(18, min(28, (height - 34) // max(rows, 1)))
        for _ in range(rows):
            self.checkbox(checkbox_x, row_y)
            self.fill_rect(line_x, row_y + 6, x + width - 24, row_y + 12, self.background)
            row_y += row_gap

    def checkbox(self, x, y):
        self.fill_rect(x, y, x + 18, y + 18, self.background)
        self.fill_rect(x + 3, y + 3, x + 15, y + 15, self.ink)
        self.draw_line(x + 5, y + 10, x + 8, y + 13, 4, self.background)
        self.draw_line(x + 8, y + 13, x + 14, y + 6, 4, self.background)

    def badge(self, cx, cy, radius):
        self.fill_circle(cx, cy, radius, self.ink)
        self.dotted_disc(cx, cy, radius - 14, 16, 4, self.background)
        self.fill_circle(cx, cy, radius - 22, self.ink)

        self.draw_line(cx - 18, cy + 2, cx - 2, cy + 18, 10, self.background)
        self.draw_line(cx - 2, cy + 18, cx + 24, cy - 14, 10, self.background)

        for offset in (-42, -28, 28, 42):
            self.draw_line(cx + offset, cy - radius - 12, cx + offset, cy - radius - 2, 6, self.ink)

        self.draw_line(cx - radius - 16, cy - 6, cx - radius - 4, cy - 6, 6, self.ink)
        self.draw_line(cx + radius + 4, cy + 6, cx + radius + 16, cy + 6, 6, self.ink)

    def save_png(self, output_path):
        def png_chunk(tag, data):
            checksum = zlib.crc32(tag + data) & 0xFFFFFFFF
            return struct.pack("!I", len(data)) + tag + data + struct.pack("!I", checksum)

        raw = bytearray()
        row_bytes = self.width * 3
        for y in range(self.height):
            raw.append(0)
            start = y * row_bytes
            raw.extend(self.pixels[start : start + row_bytes])

        ihdr = struct.pack("!IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0)
        png_data = b"".join(
            [
                b"\x89PNG\r\n\x1a\n",
                png_chunk(b"IHDR", ihdr),
                png_chunk(b"IDAT", zlib.compress(bytes(raw), level=9)),
                png_chunk(b"IEND", b""),
            ]
        )

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(png_data)


def dot_halo(canvas, rng, center_x, center_y, radius, count, radius_range=(2, 4)):
    for _ in range(count):
        angle = rng.uniform(0, math.tau)
        distance = radius * math.sqrt(rng.random())
        x = center_x + math.cos(angle) * distance
        y = center_y + math.sin(angle) * distance
        canvas.fill_circle(int(x), int(y), rng.randint(*radius_range), canvas.ink)


def wave(base, components):
    def inner(x):
        value = base
        for amplitude, frequency, phase in components:
            value += amplitude * math.sin(x * frequency + phase)
        return value

    return inner


def point(canvas, fx, fy):
    return int(canvas.width * fx), int(canvas.height * fy)


def rect(canvas, fx, fy, fw, fh):
    x, y = point(canvas, fx, fy)
    return x, y, int(canvas.width * fw), int(canvas.height * fh)


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def jitter_ratio(value, rng, amount, minimum=0.0, maximum=1.0):
    return clamp(value + rng.uniform(-amount, amount), minimum, maximum)


def draw_heart(canvas, cx, cy, size):
    canvas.fill_circle(cx - size // 2, cy, size, canvas.ink)
    canvas.fill_circle(cx + size // 2, cy, size, canvas.ink)

    for row in range(size * 2):
        width = int((size * 2 - row) * 1.3)
        canvas.fill_rect(cx - width // 2, cy + row, cx + width // 2, cy + row + 1, canvas.ink)


def draw_orb(canvas, cx, cy, radius):
    canvas.fill_circle(cx, cy, radius, canvas.ink)
    canvas.dotted_disc(cx, cy, radius - 20, 16, 4, canvas.background)
    canvas.draw_line(cx - radius - 24, cy, cx - 12, cy, 6, canvas.ink)
    canvas.draw_line(cx + 12, cy, cx + radius + 24, cy, 6, canvas.ink)
    canvas.draw_line(cx, cy - radius - 24, cx, cy - 12, 6, canvas.ink)
    canvas.draw_line(cx, cy + 12, cx, cy + radius + 24, 6, canvas.ink)


def draw_signal_panel(canvas, x, y, width, height, style, rng):
    canvas.fill_rect(x, y, x + width, y + height, canvas.ink)
    canvas.fill_rect(x + 12, y + 12, x + width - 12, y + height - 12, canvas.background)

    if style == "bars":
        bar_x = x + 24
        bar_width = max(18, width // 10)
        baseline = y + height - 26
        for _ in range(4):
            bar_height = rng.randint(height // 5, height - 48)
            canvas.fill_rect(bar_x, baseline - bar_height, bar_x + bar_width, baseline, canvas.ink)
            bar_x += bar_width + 18
        return

    if style == "tiles":
        tile_w = max(28, (width - 54) // 3)
        tile_h = max(24, (height - 52) // 2)
        start_x = x + 18
        start_y = y + 18
        for row in range(2):
            for column in range(3):
                tile_x = start_x + column * (tile_w + 6)
                tile_y = start_y + row * (tile_h + 8)
                canvas.fill_rect(tile_x, tile_y, tile_x + tile_w, tile_y + tile_h, canvas.ink)
        return

    if style == "pulse":
        chart_points = [
            (x + 18, y + height - 36),
            (x + width // 3, y + height - 52),
            (x + width // 2, y + height - 30),
            (x + width - 26, y + 28),
        ]
        for start, finish in zip(chart_points, chart_points[1:]):
            canvas.draw_line(start[0], start[1], finish[0], finish[1], 8, canvas.ink)
        for px, py in chart_points[:-1]:
            canvas.fill_circle(px, py, 7, canvas.ink)
        return

    column_x = x + 24
    for height_scale in (0.30, 0.55, 0.42):
        column_height = int((height - 44) * height_scale)
        canvas.fill_rect(column_x, y + height - 24 - column_height, column_x + 24, y + height - 24, canvas.ink)
        column_x += 38
    canvas.draw_line(x + 18, y + 34, x + width - 20, y + 34, 6, canvas.ink)


def draw_code_window(canvas, x, y, width, height, rng, rows=5, style="code"):
    canvas.fill_rect(x, y, x + width, y + height, canvas.ink)

    inset = max(8, min(width, height) // 14)
    inner_x0 = x + inset
    inner_y0 = y + inset
    inner_x1 = x + width - inset
    inner_y1 = y + height - inset
    canvas.fill_rect(inner_x0, inner_y0, inner_x1, inner_y1, canvas.background)

    header_h = max(16, height // 6)
    canvas.fill_rect(inner_x0, inner_y0, inner_x1, inner_y0 + header_h, canvas.ink)
    for dot_index in range(3):
        canvas.fill_circle(inner_x0 + 18 + dot_index * 16, inner_y0 + header_h // 2, 4, canvas.background)

    content_x = inner_x0 + 14
    content_y = inner_y0 + header_h + 12
    content_w = max(32, inner_x1 - content_x - 10)
    row_gap = max(14, min(22, (inner_y1 - content_y - 6) // max(rows, 1)))

    if style == "terminal":
        for row in range(rows):
            line_y = content_y + row * row_gap
            canvas.fill_rect(content_x, line_y, content_x + 10, line_y + 6, canvas.ink)
            line_width = rng.randint(max(24, content_w // 4), content_w)
            canvas.fill_rect(content_x + 18, line_y, content_x + 18 + line_width, line_y + 6, canvas.ink)
        return

    if style == "split":
        divider_x = x + width // 2
        canvas.fill_rect(divider_x - 2, content_y - 6, divider_x + 2, inner_y1 - 8, canvas.ink)
        left_w = divider_x - content_x - 14
        right_x = divider_x + 12
        right_w = inner_x1 - right_x - 10

        for row in range(rows):
            line_y = content_y + row * row_gap
            indent = rng.randint(0, 18)
            line_width = rng.randint(max(20, left_w // 3), max(24, left_w - 4))
            canvas.fill_rect(content_x + indent, line_y, content_x + indent + line_width, line_y + 6, canvas.ink)

        tile_h = max(16, (inner_y1 - content_y - 16) // 3)
        for row in range(3):
            tile_y = content_y + row * (tile_h + 8)
            canvas.fill_rect(right_x, tile_y, right_x + right_w, tile_y + tile_h, canvas.ink)
        return

    for row in range(rows):
        line_y = content_y + row * row_gap
        indent = rng.randint(0, 24)
        line_width = rng.randint(max(28, content_w // 3), content_w)
        canvas.fill_rect(content_x + indent, line_y, content_x + indent + line_width, line_y + 6, canvas.ink)


def draw_chip_block(canvas, x, y, width, height):
    canvas.fill_rect(x, y, x + width, y + height, canvas.ink)

    inset = max(10, min(width, height) // 5)
    core_x0 = x + inset
    core_y0 = y + inset
    core_x1 = x + width - inset
    core_y1 = y + height - inset
    canvas.fill_rect(core_x0, core_y0, core_x1, core_y1, canvas.background)
    canvas.fill_rect(core_x0 + 10, core_y0 + 10, core_x1 - 10, core_y1 - 10, canvas.ink)

    pin_len = max(10, min(width, height) // 5)
    top_spacing = max(16, width // 4)
    left_spacing = max(16, height // 4)

    for px in range(x + top_spacing, x + width, top_spacing):
        canvas.draw_line(px, y, px, y - pin_len, 6, canvas.ink)
        canvas.draw_line(px, y + height, px, y + height + pin_len, 6, canvas.ink)

    for py in range(y + left_spacing, y + height, left_spacing):
        canvas.draw_line(x, py, x - pin_len, py, 6, canvas.ink)
        canvas.draw_line(x + width, py, x + width + pin_len, py, 6, canvas.ink)


def draw_trace_flow(canvas, points, thickness=10, node_radius=10, arrow=True):
    if len(points) < 2:
        return

    for start, finish in zip(points, points[1:]):
        canvas.draw_line(start[0], start[1], finish[0], finish[1], thickness, canvas.ink)

    inner_radius = max(3, node_radius // 2)
    for x, y in points[:-1]:
        canvas.fill_circle(x, y, node_radius, canvas.ink)
        canvas.fill_circle(x, y, inner_radius, canvas.background)

    if not arrow:
        return

    prev_x, prev_y = points[-2]
    head_x, head_y = points[-1]
    arrow_size = max(18, thickness * 2)
    dx = head_x - prev_x
    dy = head_y - prev_y

    if abs(dx) >= abs(dy):
        sign = 1 if dx >= 0 else -1
        canvas.draw_line(head_x - sign * arrow_size, head_y - arrow_size // 2, head_x, head_y, thickness, canvas.ink)
        canvas.draw_line(head_x - sign * arrow_size, head_y + arrow_size // 2, head_x, head_y, thickness, canvas.ink)
        return

    sign = 1 if dy >= 0 else -1
    canvas.draw_line(head_x - arrow_size // 2, head_y - sign * arrow_size, head_x, head_y, thickness, canvas.ink)
    canvas.draw_line(head_x + arrow_size // 2, head_y - sign * arrow_size, head_x, head_y, thickness, canvas.ink)


def draw_launch(canvas, rng, seed):
    seed_value = abs(seed)
    variant = seed_value % 4
    lower_wave = wave(
        int(canvas.height * rng.uniform(0.69, 0.78)),
        [
            (rng.randint(18, 34), rng.uniform(0.008, 0.014), rng.uniform(0.0, 1.1)),
            (rng.randint(12, 24), rng.uniform(0.018, 0.032), rng.uniform(0.0, 1.8)),
        ],
    )
    ridge_top = wave(
        int(canvas.height * rng.uniform(0.33, 0.44)),
        [
            (rng.randint(16, 28), rng.uniform(0.010, 0.015), rng.uniform(0.1, 1.5)),
            (rng.randint(10, 20), rng.uniform(0.024, 0.038), rng.uniform(0.2, 2.2)),
        ],
    )
    ridge_gap = rng.randint(24, 42)
    ridge_bottom = lambda x: lower_wave(x) - ridge_gap

    halo_sets = [
        [(0.06, 0.26, 120, 220), (0.18, 0.31, 82, 110), (0.80, 0.29, 90, 140), (0.92, 0.23, 112, 180)],
        [(0.05, 0.22, 108, 180), (0.27, 0.35, 78, 100), (0.72, 0.24, 70, 90), (0.90, 0.20, 118, 190)],
        [(0.07, 0.34, 126, 210), (0.23, 0.22, 68, 80), (0.67, 0.31, 86, 120), (0.88, 0.30, 104, 160)],
        [(0.10, 0.20, 96, 150), (0.30, 0.28, 88, 120), (0.78, 0.21, 102, 150), (0.94, 0.29, 114, 190)],
    ]
    for fx, fy, radius, count in halo_sets[variant]:
        halo_x, halo_y = point(canvas, fx, fy)
        dot_halo(canvas, rng, halo_x, halo_y, radius, count)

    canvas.dotted_band(ridge_top, ridge_bottom, 16, 5, canvas.ink)

    launch_variants = [
        {
            "cards": [(0.06, 0.40, 0.14, 0.27), (0.25, 0.29, 0.14, 0.27), (0.44, 0.18, 0.14, 0.27)],
            "rows": [3, 3, 3],
            "path": [(0.09, 0.61), (0.21, 0.49), (0.35, 0.41), (0.49, 0.32), (0.63, 0.27), (0.71, 0.27)],
            "badge": (0.75, 0.27, 0.15),
        },
        {
            "cards": [(0.05, 0.47, 0.11, 0.22), (0.19, 0.37, 0.11, 0.22), (0.34, 0.27, 0.11, 0.22), (0.49, 0.16, 0.11, 0.22)],
            "rows": [2, 3, 3, 2],
            "path": [(0.10, 0.65), (0.18, 0.58), (0.31, 0.49), (0.45, 0.38), (0.61, 0.24), (0.77, 0.24)],
            "badge": (0.84, 0.24, 0.12),
        },
        {
            "cards": [(0.08, 0.50, 0.13, 0.22), (0.31, 0.42, 0.13, 0.22), (0.54, 0.34, 0.13, 0.22)],
            "rows": [3, 2, 3],
            "path": [(0.11, 0.70), (0.25, 0.66), (0.41, 0.58), (0.58, 0.49), (0.73, 0.43), (0.84, 0.43)],
            "badge": (0.90, 0.43, 0.11),
        },
        {
            "cards": [(0.06, 0.28, 0.16, 0.28), (0.33, 0.20, 0.17, 0.28)],
            "rows": [4, 4],
            "path": [(0.12, 0.53), (0.27, 0.53), (0.43, 0.42), (0.60, 0.31), (0.76, 0.31)],
            "badge": (0.85, 0.31, 0.15),
        },
    ]
    config = launch_variants[variant]

    jittered_cards = []
    for fx, fy, fw, fh in config["cards"]:
        jittered_cards.append(
            (
                jitter_ratio(fx, rng, 0.025, 0.03, 0.82),
                jitter_ratio(fy, rng, 0.035, 0.08, 0.70),
                jitter_ratio(fw, rng, 0.015, 0.10, 0.20),
                jitter_ratio(fh, rng, 0.020, 0.18, 0.32),
            )
        )

    path_points = [
        point(
            canvas,
            jitter_ratio(fx, rng, 0.020, 0.06, 0.92),
            jitter_ratio(fy, rng, 0.035, 0.16, 0.76),
        )
        for fx, fy in config["path"]
    ]
    for start, finish in zip(path_points, path_points[1:]):
        canvas.draw_line(start[0], start[1], finish[0], finish[1], 12, canvas.ink)

    canvas.draw_line(path_points[-1][0] - 34, path_points[-1][1] - 15, path_points[-1][0], path_points[-1][1], 12, canvas.ink)
    canvas.draw_line(path_points[-1][0] - 34, path_points[-1][1] + 15, path_points[-1][0], path_points[-1][1], 12, canvas.ink)

    for x, y in path_points[:-1]:
        canvas.fill_circle(x, y, 12, canvas.ink)
        canvas.fill_circle(x, y, 5, canvas.background)

    for card, rows in zip(jittered_cards, config["rows"]):
        x, y, width, height = rect(canvas, *card)
        canvas.striped_card(x, y, width, height, rows=rows)

    badge_x, badge_y = point(
        canvas,
        jitter_ratio(config["badge"][0], rng, 0.028, 0.60, 0.94),
        jitter_ratio(config["badge"][1], rng, 0.030, 0.18, 0.50),
    )
    canvas.badge(badge_x, badge_y, int(canvas.height * jitter_ratio(config["badge"][2], rng, 0.018, 0.10, 0.18)))
    canvas.fill_bottom_wave(lower_wave, canvas.ink)


def draw_signal(canvas, rng, seed):
    variant = abs(seed) % 4
    upper_band = wave(
        int(canvas.height * rng.uniform(0.28, 0.40)),
        [
            (rng.randint(16, 26), rng.uniform(0.012, 0.018), rng.uniform(0.0, 1.4)),
            (rng.randint(8, 18), rng.uniform(0.026, 0.040), rng.uniform(0.2, 2.0)),
        ],
    )
    lower_band = wave(
        int(canvas.height * rng.uniform(0.48, 0.60)),
        [
            (rng.randint(14, 24), rng.uniform(0.010, 0.016), rng.uniform(0.1, 1.8)),
            (rng.randint(8, 18), rng.uniform(0.020, 0.032), rng.uniform(0.4, 2.1)),
        ],
    )
    floor_wave = wave(
        int(canvas.height * rng.uniform(0.71, 0.78)),
        [
            (rng.randint(14, 24), rng.uniform(0.009, 0.014), rng.uniform(0.2, 1.4)),
            (rng.randint(10, 18), rng.uniform(0.018, 0.028), rng.uniform(0.6, 2.0)),
        ],
    )

    canvas.dotted_band(upper_band, lower_band, 18, 4, canvas.ink)

    signal_variants = [
        {
            "grid": (0.10, 0.16, 0.78, 0.42, 72, 48),
            "path": [(0.12, 0.50), (0.24, 0.47), (0.36, 0.55), (0.49, 0.40), (0.61, 0.53), (0.74, 0.40)],
            "panel": (0.70, 0.18, 0.16, 0.24, "bars"),
        },
        {
            "grid": (0.14, 0.14, 0.70, 0.46, 84, 44),
            "path": [(0.16, 0.40), (0.28, 0.45), (0.41, 0.63), (0.55, 0.47), (0.69, 0.31), (0.80, 0.27)],
            "panel": (0.08, 0.20, 0.16, 0.26, "tiles"),
        },
        {
            "grid": (0.09, 0.20, 0.74, 0.38, 64, 52),
            "path": [(0.11, 0.58), (0.25, 0.57), (0.25, 0.46), (0.41, 0.46), (0.41, 0.34), (0.59, 0.34), (0.59, 0.25), (0.77, 0.25)],
            "panel": (0.73, 0.12, 0.15, 0.30, "pulse"),
        },
        {
            "grid": (0.08, 0.16, 0.80, 0.44, 72, 46),
            "path": [(0.12, 0.60), (0.24, 0.34), (0.36, 0.48), (0.49, 0.29), (0.63, 0.46), (0.78, 0.24)],
            "panel": (0.72, 0.19, 0.15, 0.25, "columns"),
        },
    ]
    config = signal_variants[variant]

    grid_x, grid_y, grid_w, grid_h, grid_step_x, grid_step_y = config["grid"]
    grid_x = jitter_ratio(grid_x, rng, 0.02, 0.05, 0.20)
    grid_y = jitter_ratio(grid_y, rng, 0.03, 0.08, 0.24)
    grid_w = jitter_ratio(grid_w, rng, 0.04, 0.62, 0.84)
    grid_h = jitter_ratio(grid_h, rng, 0.03, 0.34, 0.52)
    start_x, start_y = point(canvas, grid_x, grid_y)
    grid_width = int(canvas.width * grid_w)
    grid_height = int(canvas.height * grid_h)
    for x in range(start_x, start_x + grid_width, grid_step_x):
        canvas.fill_rect(x, start_y, x + 4, start_y + grid_height, canvas.ink)
    for y in range(start_y, start_y + grid_height, grid_step_y):
        canvas.fill_rect(start_x, y, start_x + grid_width, y + 4, canvas.ink)

    points = [
        point(
            canvas,
            jitter_ratio(fx, rng, 0.022, 0.08, 0.90),
            jitter_ratio(fy, rng, 0.040, 0.20, 0.70),
        )
        for fx, fy in config["path"]
    ]
    for start, finish in zip(points, points[1:]):
        canvas.draw_line(start[0], start[1], finish[0], finish[1], 12, canvas.ink)

    canvas.draw_line(points[-1][0] - 30, points[-1][1] - 14, points[-1][0], points[-1][1], 12, canvas.ink)
    canvas.draw_line(points[-1][0] - 28, points[-1][1] + 16, points[-1][0], points[-1][1], 12, canvas.ink)

    for x, y in points[:-1]:
        canvas.fill_circle(x, y, 12, canvas.ink)
        canvas.fill_circle(x, y, 5, canvas.background)

    panel_x, panel_y, panel_w, panel_h, panel_style = config["panel"]
    panel_rect = rect(
        canvas,
        jitter_ratio(panel_x, rng, 0.025, 0.05, 0.78),
        jitter_ratio(panel_y, rng, 0.030, 0.08, 0.30),
        jitter_ratio(panel_w, rng, 0.018, 0.12, 0.22),
        jitter_ratio(panel_h, rng, 0.022, 0.20, 0.34),
    )
    draw_signal_panel(canvas, *panel_rect, panel_style, rng)

    canvas.fill_bottom_wave(floor_wave, canvas.ink)


def draw_summit(canvas, rng, seed):
    variant = abs(seed) % 4
    far_top = wave(
        int(canvas.height * rng.uniform(0.24, 0.34)),
        [
            (rng.randint(14, 22), rng.uniform(0.011, 0.017), rng.uniform(0.1, 1.4)),
            (rng.randint(8, 14), rng.uniform(0.020, 0.032), rng.uniform(0.3, 1.8)),
        ],
    )
    far_bottom = wave(
        int(canvas.height * rng.uniform(0.42, 0.52)),
        [
            (rng.randint(12, 20), rng.uniform(0.010, 0.015), rng.uniform(0.2, 1.6)),
            (rng.randint(8, 14), rng.uniform(0.020, 0.030), rng.uniform(0.8, 2.0)),
        ],
    )
    near_top = wave(
        int(canvas.height * rng.uniform(0.52, 0.60)),
        [
            (rng.randint(14, 22), rng.uniform(0.010, 0.015), rng.uniform(0.2, 1.2)),
            (rng.randint(10, 16), rng.uniform(0.018, 0.026), rng.uniform(0.4, 1.9)),
        ],
    )

    canvas.dotted_band(far_top, far_bottom, 18, 4, canvas.ink)

    summit_variants = [
        {
            "ridge": [(0.00, 0.58), (0.14, 0.42), (0.27, 0.58), (0.41, 0.34), (0.55, 0.60), (0.72, 0.43), (1.00, 0.66)],
            "trail": [(0.11, 0.74), (0.23, 0.67), (0.33, 0.60), (0.41, 0.47)],
            "flag": (0.41, 0.34),
            "halos": [(0.14, 0.24, 96, 140), (0.84, 0.21, 118, 170)],
        },
        {
            "ridge": [(0.00, 0.62), (0.10, 0.48), (0.22, 0.61), (0.35, 0.36), (0.50, 0.58), (0.63, 0.31), (0.78, 0.56), (1.00, 0.60)],
            "trail": [(0.15, 0.76), (0.25, 0.70), (0.34, 0.61), (0.44, 0.50), (0.55, 0.42), (0.63, 0.35)],
            "flag": (0.63, 0.31),
            "halos": [(0.20, 0.23, 104, 160), (0.74, 0.18, 94, 130)],
        },
        {
            "ridge": [(0.00, 0.64), (0.18, 0.46), (0.34, 0.59), (0.54, 0.40), (0.70, 0.28), (0.84, 0.55), (1.00, 0.48)],
            "trail": [(0.08, 0.75), (0.22, 0.70), (0.36, 0.61), (0.52, 0.52), (0.66, 0.36)],
            "flag": (0.70, 0.28),
            "halos": [(0.12, 0.20, 90, 120), (0.88, 0.25, 126, 190)],
        },
        {
            "ridge": [(0.00, 0.56), (0.16, 0.34), (0.30, 0.54), (0.46, 0.46), (0.60, 0.62), (0.74, 0.40), (0.88, 0.58), (1.00, 0.53)],
            "trail": [(0.07, 0.73), (0.18, 0.62), (0.29, 0.54), (0.39, 0.46), (0.49, 0.43)],
            "flag": (0.16, 0.34),
            "halos": [(0.10, 0.18, 110, 170), (0.66, 0.26, 90, 120), (0.91, 0.16, 78, 100)],
        },
    ]
    config = summit_variants[variant]
    ridge_points = []
    for index, (fx, fy) in enumerate(config["ridge"]):
        if index == 0 or index == len(config["ridge"]) - 1:
            ridge_points.append(point(canvas, fx, jitter_ratio(fy, rng, 0.020, 0.20, 0.80)))
            continue
        ridge_points.append(
            point(
                canvas,
                jitter_ratio(fx, rng, 0.025, 0.06, 0.94),
                jitter_ratio(fy, rng, 0.045, 0.24, 0.70),
            )
        )

    for start, finish in zip(ridge_points, ridge_points[1:]):
        canvas.draw_line(start[0], start[1], finish[0], finish[1], 26, canvas.ink)

    canvas.fill_bottom_wave(near_top, canvas.ink)

    trail_points = [
        point(
            canvas,
            jitter_ratio(fx, rng, 0.018, 0.04, 0.90),
            jitter_ratio(fy, rng, 0.030, 0.30, 0.84),
        )
        for fx, fy in config["trail"]
    ]
    for start, finish in zip(trail_points, trail_points[1:]):
        canvas.draw_line(start[0], start[1], finish[0], finish[1], 10, canvas.background)
    for x, y in trail_points[:-1]:
        canvas.fill_circle(x, y, 10, canvas.background)

    peak_x, peak_y = point(
        canvas,
        jitter_ratio(config["flag"][0], rng, 0.018, 0.06, 0.92),
        jitter_ratio(config["flag"][1], rng, 0.028, 0.20, 0.60),
    )
    canvas.draw_line(peak_x, peak_y, peak_x, peak_y - 42, 8, canvas.background)
    canvas.draw_line(peak_x, peak_y - 42, peak_x + 30, peak_y - 28, 8, canvas.background)
    canvas.draw_line(peak_x + 30, peak_y - 28, peak_x, peak_y - 18, 8, canvas.background)

    for fx, fy, radius, count in config["halos"]:
        halo_x, halo_y = point(canvas, fx, fy)
        dot_halo(canvas, rng, halo_x, halo_y, radius, count)


def draw_reflection(canvas, rng, seed):
    variant = abs(seed) % 4
    floor_wave = wave(
        int(canvas.height * rng.uniform(0.74, 0.82)),
        [
            (rng.randint(16, 24), rng.uniform(0.009, 0.013), rng.uniform(0.0, 1.6)),
            (rng.randint(10, 18), rng.uniform(0.018, 0.028), rng.uniform(0.2, 2.0)),
        ],
    )
    ribbon_top = wave(
        int(canvas.height * rng.uniform(0.36, 0.48)),
        [
            (rng.randint(14, 24), rng.uniform(0.010, 0.014), rng.uniform(0.2, 1.4)),
            (rng.randint(8, 14), rng.uniform(0.024, 0.038), rng.uniform(0.8, 2.4)),
        ],
    )
    ribbon_gap = rng.randint(34, 56)
    ribbon_bottom = lambda x: ribbon_top(x) + ribbon_gap

    canvas.dotted_band(ribbon_top, ribbon_bottom, 16, 4, canvas.ink)

    reflection_variants = [
        {
            "hearts": [(0.25, 0.30, 0.22)],
            "orbs": [(0.77, 0.31, 62)],
            "halos": [(0.25, 0.41, 150, 180)],
        },
        {
            "hearts": [(0.72, 0.31, 0.20)],
            "orbs": [(0.22, 0.28, 54)],
            "halos": [(0.76, 0.40, 138, 170), (0.16, 0.20, 92, 110)],
        },
        {
            "hearts": [(0.48, 0.28, 0.19)],
            "orbs": [(0.80, 0.24, 48)],
            "halos": [(0.48, 0.40, 126, 150), (0.15, 0.26, 86, 100)],
        },
        {
            "hearts": [(0.31, 0.32, 0.15), (0.43, 0.26, 0.12)],
            "orbs": [(0.74, 0.29, 58)],
            "halos": [(0.33, 0.41, 112, 130), (0.82, 0.18, 104, 140)],
        },
    ]
    config = reflection_variants[variant]

    for fx, fy, size_ratio in config["hearts"]:
        heart_x, heart_y = point(
            canvas,
            jitter_ratio(fx, rng, 0.030, 0.10, 0.84),
            jitter_ratio(fy, rng, 0.030, 0.16, 0.50),
        )
        heart_size = int(canvas.height * jitter_ratio(size_ratio, rng, 0.025, 0.10, 0.26))
        draw_heart(canvas, heart_x, heart_y, heart_size)

    for fx, fy, radius in config["orbs"]:
        orb_x, orb_y = point(
            canvas,
            jitter_ratio(fx, rng, 0.030, 0.10, 0.88),
            jitter_ratio(fy, rng, 0.030, 0.14, 0.48),
        )
        draw_orb(canvas, orb_x, orb_y, int(radius * rng.uniform(0.90, 1.12)))

    for fx, fy, radius, count in config["halos"]:
        halo_x, halo_y = point(canvas, fx, fy)
        dot_halo(canvas, rng, halo_x, halo_y, radius, count, radius_range=(2, 3))

    canvas.fill_bottom_wave(floor_wave, canvas.ink)


def draw_engineering(canvas, rng, seed):
    variant = abs(seed) % 4
    floor_wave = wave(
        int(canvas.height * rng.uniform(0.72, 0.80)),
        [
            (rng.randint(14, 24), rng.uniform(0.009, 0.014), rng.uniform(0.0, 1.5)),
            (rng.randint(10, 18), rng.uniform(0.018, 0.028), rng.uniform(0.2, 2.1)),
        ],
    )
    trace_top = wave(
        int(canvas.height * rng.uniform(0.30, 0.40)),
        [
            (rng.randint(12, 22), rng.uniform(0.010, 0.016), rng.uniform(0.1, 1.8)),
            (rng.randint(8, 14), rng.uniform(0.022, 0.034), rng.uniform(0.3, 2.2)),
        ],
    )
    trace_gap = rng.randint(36, 54)
    trace_bottom = lambda x: trace_top(x) + trace_gap

    canvas.dotted_band(trace_top, trace_bottom, 16, 4, canvas.ink)

    engineering_variants = [
        {
            "windows": [
                (0.06, 0.14, 0.30, 0.28, "code", 6),
                (0.10, 0.55, 0.20, 0.16, "terminal", 3),
            ],
            "chip": (0.74, 0.26, 0.16, 0.20),
            "flow": [(0.18, 0.62), (0.40, 0.62), (0.40, 0.46), (0.62, 0.46), (0.62, 0.36), (0.72, 0.36)],
            "traces": [
                [(0.16, 0.24), (0.50, 0.24), (0.50, 0.42)],
                [(0.32, 0.58), (0.55, 0.58), (0.55, 0.28)],
            ],
            "halos": [(0.16, 0.18, 88, 120), (0.82, 0.20, 108, 160)],
        },
        {
            "windows": [
                (0.46, 0.12, 0.30, 0.28, "split", 5),
                (0.08, 0.22, 0.22, 0.18, "terminal", 4),
            ],
            "chip": (0.16, 0.54, 0.18, 0.18),
            "flow": [(0.24, 0.54), (0.24, 0.40), (0.44, 0.40), (0.44, 0.26), (0.76, 0.26)],
            "traces": [
                [(0.22, 0.60), (0.58, 0.60), (0.58, 0.44)],
                [(0.30, 0.18), (0.86, 0.18)],
            ],
            "halos": [(0.20, 0.62, 98, 130), (0.70, 0.14, 118, 170)],
        },
        {
            "windows": [
                (0.18, 0.12, 0.42, 0.24, "code", 6),
                (0.68, 0.52, 0.18, 0.16, "terminal", 3),
            ],
            "chip": (0.08, 0.50, 0.16, 0.18),
            "flow": [(0.16, 0.58), (0.34, 0.58), (0.34, 0.44), (0.58, 0.44), (0.58, 0.60), (0.68, 0.60)],
            "traces": [
                [(0.24, 0.24), (0.72, 0.24)],
                [(0.50, 0.24), (0.50, 0.56)],
            ],
            "halos": [(0.12, 0.54, 90, 120), (0.74, 0.58, 84, 110)],
        },
        {
            "windows": [
                (0.06, 0.16, 0.24, 0.24, "split", 4),
                (0.62, 0.14, 0.26, 0.26, "code", 5),
                (0.38, 0.54, 0.18, 0.16, "terminal", 3),
            ],
            "chip": (0.40, 0.24, 0.18, 0.18),
            "flow": [(0.18, 0.46), (0.40, 0.46), (0.40, 0.34), (0.58, 0.34), (0.58, 0.24), (0.72, 0.24)],
            "traces": [
                [(0.12, 0.60), (0.82, 0.60)],
                [(0.26, 0.28), (0.26, 0.60)],
                [(0.72, 0.24), (0.72, 0.60)],
            ],
            "halos": [(0.14, 0.18, 86, 110), (0.50, 0.18, 74, 90), (0.84, 0.18, 86, 120)],
        },
    ]
    config = engineering_variants[variant]

    for trace in config["traces"]:
        jittered_trace = [
            point(
                canvas,
                jitter_ratio(fx, rng, 0.016, 0.04, 0.94),
                jitter_ratio(fy, rng, 0.022, 0.12, 0.72),
            )
            for fx, fy in trace
        ]
        draw_trace_flow(canvas, jittered_trace, thickness=6, node_radius=6, arrow=False)

    for fx, fy, fw, fh, style, rows in config["windows"]:
        x, y, width, height = rect(
            canvas,
            jitter_ratio(fx, rng, 0.022, 0.04, 0.82),
            jitter_ratio(fy, rng, 0.028, 0.08, 0.66),
            jitter_ratio(fw, rng, 0.018, 0.14, 0.44),
            jitter_ratio(fh, rng, 0.018, 0.14, 0.32),
        )
        draw_code_window(canvas, x, y, width, height, rng, rows=rows, style=style)

    chip_x, chip_y, chip_w, chip_h = rect(
        canvas,
        jitter_ratio(config["chip"][0], rng, 0.022, 0.05, 0.82),
        jitter_ratio(config["chip"][1], rng, 0.028, 0.16, 0.68),
        jitter_ratio(config["chip"][2], rng, 0.018, 0.12, 0.24),
        jitter_ratio(config["chip"][3], rng, 0.018, 0.14, 0.24),
    )
    draw_chip_block(canvas, chip_x, chip_y, chip_w, chip_h)

    flow_points = [
        point(
            canvas,
            jitter_ratio(fx, rng, 0.020, 0.06, 0.92),
            jitter_ratio(fy, rng, 0.028, 0.18, 0.72),
        )
        for fx, fy in config["flow"]
    ]
    draw_trace_flow(canvas, flow_points, thickness=10, node_radius=9, arrow=True)

    for fx, fy, radius, count in config["halos"]:
        halo_x, halo_y = point(canvas, fx, fy)
        dot_halo(canvas, rng, halo_x, halo_y, radius, count)

    canvas.fill_bottom_wave(floor_wave, canvas.ink)


PRESETS = {
    "launch": {
        "description": "Workflow and checklist banner for deployments, releases, and operational playbooks.",
        "renderer": draw_launch,
        "default_output": "assets/postbg/go-live-spellbook.png",
    },
    "signal": {
        "description": "Telemetry and rising graph banner for performance, metrics, analytics, and engineering posts.",
        "renderer": draw_signal,
        "default_output": "assets/postbg/signal-banner.png",
    },
    "engineering": {
        "description": "Code workflow, systems design, computer science, and engineering process banner.",
        "renderer": draw_engineering,
        "default_output": "assets/postbg/engineering-banner.png",
    },
    "summit": {
        "description": "Mountain and trail banner for challenge, growth, roadmap, and journey-style writing.",
        "renderer": draw_summit,
        "default_output": "assets/postbg/summit-banner.png",
    },
    "reflection": {
        "description": "Abstract heart-and-orbit banner for personal, reflective, and human-centered posts.",
        "renderer": draw_reflection,
        "default_output": "assets/postbg/reflection-banner.png",
    },
}


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate monochrome post header PNGs that match this blog's visual style.",
        epilog=(
            "Examples:\n"
            "  python3 tools/generate_post_banner.py\n"
            "  python3 tools/generate_post_banner.py --preset summit --output assets/postbg/my-journey.png\n"
            "  python3 tools/generate_post_banner.py --preset signal --seed 7 --background '#E7E9EC'\n"
            "  python3 tools/generate_post_banner.py --preset engineering --output assets/postbg/systems-design.png --seed 2\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--preset",
        choices=sorted(PRESETS.keys()),
        default="launch",
        help="visual preset to render",
    )
    parser.add_argument(
        "--output",
        help="output PNG path; relative paths are resolved from the repository root",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=DEFAULT_WIDTH,
        help=f"image width in pixels (default: {DEFAULT_WIDTH})",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=DEFAULT_HEIGHT,
        help=f"image height in pixels (default: {DEFAULT_HEIGHT})",
    )
    parser.add_argument(
        "--background",
        type=parse_color,
        default=parse_color(DEFAULT_BG),
        help=f"background hex color (default: {DEFAULT_BG})",
    )
    parser.add_argument(
        "--ink",
        type=parse_color,
        default=parse_color(DEFAULT_INK),
        help=f"foreground hex color (default: {DEFAULT_INK})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="seed for deterministic layout and detail variations within a preset",
    )
    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="print the available presets and exit",
    )
    return parser


def list_presets():
    for name, config in PRESETS.items():
        print(f"{name}: {config['description']}")


def validate_size(width, height):
    if width <= 0 or height <= 0:
        raise SystemExit("width and height must be positive integers")


def resolve_output_path(output_path, fallback_path):
    selected = Path(output_path) if output_path else Path(fallback_path)
    return selected if selected.is_absolute() else REPO_ROOT / selected


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.list_presets:
        list_presets()
        return

    validate_size(args.width, args.height)

    preset = PRESETS[args.preset]
    output = resolve_output_path(args.output, preset["default_output"])

    canvas = Canvas(args.width, args.height, args.background, args.ink)
    rng = random.Random(args.seed)

    preset["renderer"](canvas, rng, args.seed)
    canvas.save_png(output)

    print(f"Generated {output} using preset '{args.preset}' with seed {args.seed}")


if __name__ == "__main__":
    main()
