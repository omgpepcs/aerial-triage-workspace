import random
from PIL import Image, ImageDraw, ImageFont

class VictimMap:
    def __init__(
        self,
        font_path: str = "C:/Windows/Fonts/arialbd.ttf",
        font_size: int = 32,
        radius_dot: int = 12,
        color_dot: str = "red",
        color_text: str = "white",
        color_bg_text: str = "red",
        coords_range: tuple[float, float] = (-25, 25),
    ):
        self.coords = []
        self.radius_dot = radius_dot
        self.color_dot = color_dot
        self.color_text = color_text
        self.color_bg_text = color_bg_text
        self.coords_range = coords_range

        try:
            self.font = ImageFont.truetype(font_path, font_size)
        except OSError:
            self.font = ImageFont.load_default()

    def _normalize(self, x: float, y: float, width: int, height: int) -> tuple[int, int]:
        coord_min, coord_max = self.coords_range
        coord_range = coord_max - coord_min
        px = int((x - coord_min) / coord_range * width)
        py = int((y - coord_min) / coord_range * height)
        return px, py

    def _draw_dot(self, draw: ImageDraw, cx: int, cy: int):
        r = self.radius_dot
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            fill=self.color_dot,
            outline="white",
            width=2,
        )

    def _draw_label(self, draw: ImageDraw, cx: int, cy: int, label: str, color: str):
        bbox = draw.textbbox((0, 0), label, font=self.font)
        width_text = bbox[2] - bbox[0]
        height_text  = bbox[3] - bbox[1]
        offset_x    = bbox[0]
        offset_y    = bbox[1]

        margin = 4
        tx = cx - width_text // 2
        ty = cy - self.radius_dot - height_text - margin * 2 - 4

        draw.rectangle(
            [tx - margin, ty - margin, tx + width_text + margin, ty + height_text + margin],
            fill=color,
        )
        draw.text((tx - offset_x, ty - offset_y), label, fill=self.color_text, font=self.font)

    def normalize_coords(self, x, y):
        x = max(-15.0, min(15.0, x))
        y = max(-15.0, min(15.0, y))
        while (x, y) in self.coords:
            x = round(random.uniform(-15, 15), 1)
            y = round(random.uniform(-15, 15), 1)
        c = (x, y)
        self.coords.append(c)
        return x, y

    def clean_coords(self):
        self.coords = []

    def export_map(
        self,
        path_img_in: str,
        path_img_out: str,
        queue: dict
    ):
        coords = []
        for id in queue.keys():
            x = queue[id]["coord_x"]
            y = queue[id]["coord_y"]
            score = queue[id]["score"]
            if score < 3:
                self.color_bg_text = "green"
            elif score < 5:
                self.color_bg_text = "yellow"
            elif score < 8:
                self.color_bg_text = "orange"
            else:
                self.color_bg_text = "red"
            coords.append((x,  y, f"{id}\nX: {x}\nY: {y}", self.color_bg_text))

        img = Image.open(path_img_in).convert("RGBA")
        width, height = img.size

        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        for x, y, label, color in coords:
            cx, cy = self._normalize(x, y, width, height)
            self._draw_dot(draw, cx, cy)
            self._draw_label(draw, cx, cy, label, color)

        result = Image.alpha_composite(img, overlay).convert("RGB")
        result.save(path_img_out)
