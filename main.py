import cv2
from video_feed import VideoFeed
from draw_zones import ZoneDrawer

drawer = ZoneDrawer()
feed = VideoFeed(0)

cv2.namedWindow("Milestone 1")
cv2.setMouseCallback("Milestone 1", drawer.mouse_callback)

print("\nControls:")
print("Draw: Drag mouse")
print("Move: Drag inside")
print("Resize: Drag corners")
print("S = Save zones")
print("L = Load zones")
print("D = Delete selected")
print("C = Clear all zones")
print("Q = Quit\n")

while True:
    frame = feed.get_frame()
    if frame is None:
        break

    view = drawer.draw(frame)
    cv2.imshow("Milestone 1", view)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('s'): drawer.save()
    elif key == ord('l'): drawer.load()
    elif key == ord('d'):
        if drawer.selected is not None:
            drawer.zones.pop(drawer.selected)
            drawer.selected = None
            print("✔ Deleted")
    elif key == ord('c'):
        drawer.zones = []
        drawer.selected = None
        print("✔ Cleared")
    elif key == ord('q'):
        break

feed.release()
