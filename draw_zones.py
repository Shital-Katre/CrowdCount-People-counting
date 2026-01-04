import cv2
from zone_storage import save_zones, load_zones, normalize

CORNER_THRESHOLD = 10

class ZoneDrawer:
    def __init__(self):
        self.zones = []
        self.selected = None
        self.hover = None

        self.drawing = False
        self.dragging = False
        self.resizing = False

        self.start_x = self.start_y = 0
        self.mx = self.my = 0

        self.resize_corner = None
        self.offset_x = self.offset_y = 0

    def inside(self, x, y, z):
        return z[0] <= x <= z[2] and z[1] <= y <= z[3]

    def corner_hit(self, x, y, z):
        corners = [
            (z[0], z[1]),
            (z[2], z[1]),
            (z[0], z[3]),
            (z[2], z[3])
        ]
        for i, (cx, cy) in enumerate(corners):
            if abs(x - cx) <= CORNER_THRESHOLD and abs(y - cy) <= CORNER_THRESHOLD:
                return i
        return None

    def mouse_callback(self, event, x, y, flags, param):
        self.mx, self.my = x, y

        # hover check
        self.hover = None
        for i in reversed(range(len(self.zones))):
            if self.inside(x, y, self.zones[i]):
                self.hover = i
                break

        if event == cv2.EVENT_LBUTTONDOWN:

            # Resize check
            for i in reversed(range(len(self.zones))):
                c = self.corner_hit(x, y, self.zones[i])
                if c is not None:
                    self.selected = i
                    self.resizing = True
                    self.resize_corner = c
                    return

            # Drag check
            for i in reversed(range(len(self.zones))):
                if self.inside(x, y, self.zones[i]):
                    self.selected = i
                    self.dragging = True
                    self.offset_x = x - self.zones[i][0]
                    self.offset_y = y - self.zones[i][1]
                    return

            # New zone
            self.drawing = True
            self.start_x = x
            self.start_y = y
            self.selected = None

        elif event == cv2.EVENT_MOUSEMOVE:

            if self.dragging and self.selected is not None:
                z = self.zones[self.selected]
                w, h = z[2] - z[0], z[3] - z[1]
                self.zones[self.selected] = [
                    x - self.offset_x,
                    y - self.offset_y,
                    x - self.offset_x + w,
                    y - self.offset_y + h
                ]

            if self.resizing and self.selected is not None:
                z = self.zones[self.selected]
                if self.resize_corner == 0: z[0], z[1] = x, y
                elif self.resize_corner == 1: z[2], z[1] = x, y
                elif self.resize_corner == 2: z[0], z[3] = x, y
                elif self.resize_corner == 3: z[2], z[3] = x, y

        elif event == cv2.EVENT_LBUTTONUP:

            if self.drawing:
                self.drawing = False
                new_zone = normalize([self.start_x, self.start_y, x, y])
                self.zones.append(new_zone)
                self.selected = len(self.zones) - 1

            self.dragging = False
            self.resizing = False
            self.resize_corner = None

    def draw(self, frame):
        view = frame.copy()

        # Live drawing
        if self.drawing:
            cv2.rectangle(view, (self.start_x, self.start_y), (self.mx, self.my), (0, 255, 0), 1)

        for i, z in enumerate(self.zones):
            z = normalize(z)
            color = (0, 0, 255)
            thick = 2

            if self.selected == i:
                color = (0, 255, 0)
                thick = 3
            elif self.hover == i:
                color = (0, 200, 0)

            cv2.rectangle(view, (z[0], z[1]), (z[2], z[3]), color, thick)

            # Corner indicators
            corners = [
                (z[0], z[1]), (z[2], z[1]),
                (z[0], z[3]), (z[2], z[3])
            ]
            for cx, cy in corners:
                cv2.rectangle(view, (cx - 4, cy - 4), (cx + 4, cy + 4), color, -1)

        return view

    def save(self):
        save_zones(self.zones)

    def load(self):
        self.zones = load_zones()