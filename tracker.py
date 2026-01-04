import math

class SimpleTracker:
    def __init__(self):
        self.objects = {}
        self.next_id = 1

    def update(self, detections):
        new_objects = {}

        for box in detections:
            x1,y1,x2,y2 = box
            cx, cy = int((x1+x2)/2), int((y1+y2)/2)

            matched = False
            for obj_id, (px,py) in self.objects.items():
                if math.dist((cx,cy),(px,py)) < 50:
                    new_objects[obj_id] = (cx,cy)
                    matched = True
                    break

            if not matched:
                new_objects[self.next_id] = (cx,cy)
                self.next_id += 1

        self.objects = new_objects
        return self.objects
