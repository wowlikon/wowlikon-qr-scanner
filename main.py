#usr/bin/python3 
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.camera import Camera
from kivy.utils import platform
from kivy.lang import Builder
from kivy.clock import Clock
import cv2, time, traceback
from kivy.app import App
import numpy as np

if platform == "android":
    from android.permissions import check_permission, request_permissions, Permission
    request_permissions([Permission.CAMERA, Permission.INTERNET])
    while not check_permission(Permission.CAMERA): time.sleep(0.1)

try: Builder.load_file('ui.kv')
except Exception:
    e = traceback.format_exc()
    with open('err.kv', 'r') as f:
        s = f.read().format(err=repr(e))
        root = Builder.load_string(s)

class AndroidCamera(Camera):
    camera_resolution = (640, 480)
    cam_ratio = camera_resolution[0] / camera_resolution[1]

class MyLayout(BoxLayout):
    def build(self):
        return root

class MyApp(App):
    period = 1 #75 chars max
    d = cv2.QRCodeDetector()

    def build(self):
        return MyLayout()

    def on_start(self):
        Clock.schedule_once(self.get_frame, 5)

    def get_frame(self, dt):
        ts = time.time()
        try:
            cam = self.root.ids.a_cam
            image_object = cam.export_as_image(scale=round((400 / int(cam.height)), 2))
            w, h = image_object._texture.size
            frame = np.frombuffer(image_object._texture.pixels, 'uint8').reshape(h, w, 4)
            gray = cv2.cvtColor(frame, cv2.COLOR_RGBA2GRAY)
            text, points, _ = self.d.detectAndDecode(gray)
            self.root.ids.fps_text.text = f'FPS: {(1/self.period):.2f}'
            self.root.ids.text_out.text = f'Text {(": "+text) if text else "not found"}'
            self.root.ids.fps_text.font_size = self.root.height//(10 * len(self.root.ids.fps_text.text)) * 2
            self.root.ids.text_out.font_size = self.root.height//(10 * len(self.root.ids.text_out.text)) * 8 + 2
            Clock.schedule_once(self.get_frame, 0.25)
        except Exception as exception:
            self.root.ids.fps_text.text = f'FPS: {(1/self.period):.2f}'
            self.root.ids.text_out.text = f'Error: {exception}'
        te = time.time()
        self.period = (te - ts)

if __name__ == "__main__":
    MyApp().run()