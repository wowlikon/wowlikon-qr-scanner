#usr/bin/python3 
from kivy.core.clipboard import Clipboard
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.camera import Camera
from kivy.utils import platform
import cv2, time, traceback, re
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.app import App
import numpy as np

if platform == "android": #buildozer android debug deploy run logcat (run with adb logcat)
    from android.permissions import check_permission, request_permissions, Permission
    request_permissions([Permission.CAMERA, Permission.INTERNET])
    while not check_permission(Permission.CAMERA): time.sleep(0.1)

def launch_webbrowser(url):
    import webbrowser
    if platform == 'android':
        from jnius import autoclass, cast
        def open_url(url):
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            browserIntent = Intent()
            browserIntent.setAction(Intent.ACTION_VIEW)
            browserIntent.setData(Uri.parse(url))
            currentActivity = cast('android.app.Activity', activity)
            currentActivity.startActivity(browserIntent)

        # Web browser support.
        class AndroidBrowser(object):
            def open(self, url, new=0, autoraise=True): open_url(url)
            def open_new(self, url): open_url(url)
            def open_new_tab(self, url): open_url(url)
        webbrowser.register('android', AndroidBrowser)
    webbrowser.open(url)

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

    def interact(self):
        if self.res:
            if re.search(r"[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)", self.res):
                launch_webbrowser(self.res)
            else:
                Clipboard.copy(self.res)

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
            self.res = text if text else ''
            text = text[:50] + (text[50:] and '...')
            self.root.ids.text_out.interact = self.interact
            self.root.ids.fps_text.text = f'FPS: {(1/self.period):.2f}'
            if not text: self.root.ids.text_out.text = 'QR-code not found'
            elif re.search(r"[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)", text):
                self.root.ids.text_out.text = f'Link: {text}'
            else: self.root.ids.text_out.text = f'Text: {text}'
            self.root.ids.fps_text.font_size = self.root.height//(10 * len(self.root.ids.fps_text.text)) * 2
            self.root.ids.text_out.font_size = self.root.height//(5  * len(self.root.ids.text_out.text)) * 4 + 2
            Clock.schedule_once(self.get_frame, 0.25)
        except Exception as exception:
            self.root.ids.fps_text.text = f'FPS: {(1/self.period):.2f}'
            self.root.ids.text_out.text = f'Error: {exception}'
        te = time.time()
        self.period = (te - ts)

if __name__ == "__main__":
    MyApp().run()