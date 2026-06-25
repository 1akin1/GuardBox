from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFlatButton
from kivymd.uix.card import MDCard
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window
from plyer import notification
from kivy.uix.scrollview import ScrollView
import os
import sys
import threading
import time

# Make the sibling `chatbot` package importable, then reuse its model + Firebase.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "chatbot"))
from chatbot import get_response  # noqa: E402  (import-safe: loads model only)
from firebase_config import get_db  # noqa: E402

# Window size
Window.size = (1000, 600)

# Shared Firebase handle (credentials come from environment variables;
# see chatbot/firebase_config.py and .env.example).
db = get_db()
WEIGHT_THRESHOLD = 1000  # threshold

class TopBar(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = "60dp"
        self.padding = [15, 10]
        self.md_bg_color = (0.05, 0.05, 0.1, 1)  

        # Logo
        self.logo = Image(
            source="logo.jpg",
            size_hint=(None, None),
            size=("40dp", "40dp"),
            allow_stretch=True
        )
        self.add_widget(self.logo)

        # App Title
        self.title = MDLabel(
            text="GuardBox",
            font_style="H6",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            halign="left",
            valign="middle",
            size_hint_x=None,
            width="150dp",
            padding=(10, 0)
        )
        self.add_widget(self.title)

        self.add_widget(Widget())  # Spacer

        # Theme Toggle Button
        self.theme_toggle = MDRaisedButton(
            text="Dark Mode",
            md_bg_color=(0.2, 0.5, 1, 1),
            size_hint=(None, None),
            size=("140dp", "40dp"),
            pos_hint={"center_y": 0.5},
            on_release=self.toggle_theme
        )
        self.add_widget(self.theme_toggle)

    def toggle_theme(self, *args):
        app = MDApp.get_running_app()
        if app.theme_cls.theme_style == "Dark":
            app.theme_cls.theme_style = "Light"
            self.theme_toggle.text = "Light Mode"
        else:
            app.theme_cls.theme_style = "Dark"
            self.theme_toggle.text = "Dark Mode"


class MainScreen(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.orientation = "vertical"
        self.spacing = 15
        self.padding = [20, 10]

        # Top Bar 
        self.add_widget(TopBar())

        #  Middle Cards 
        cards = MDBoxLayout(
            orientation="horizontal",
            spacing=20,
            size_hint_y=None,
            height="220dp"
        )

        # Box Status Card 
        self.status_card = MDCard(
            orientation="vertical",
            padding=20,
            radius=[15, 15, 15, 15],
            md_bg_color=(0.1, 0.1, 0.15, 1),
            size_hint=(0.5, 1)
        )

        self.status_title = MDLabel(
            text="Box Status",
            halign="center",
            font_style="H4",
            theme_text_color="Custom",
            text_color=(0.5, 0.7, 1, 1),
            size_hint_y=None,
            height="180dp"
        )

        self.box_icon_and_text = MDBoxLayout(
            orientation="horizontal",
            spacing=10,
            size_hint=(None, None),
            width="180dp",
            height="60dp",
            pos_hint={"center_x": 0.5}
        )

        self.box_image = Image(
            source="box.png",
            size_hint=(None, None),
            size=("40dp", "40dp"),
            size_hint_y=None,
            height="180dp"
        )

        self.status_label = MDLabel(
            text="Empty",
            font_style="H5",
            theme_text_color="Custom",
            text_color=(0.5, 1, 0.5, 1),
            valign="middle",
            size_hint=(1, 1),
            size_hint_y=None,
            height="180dp"
        )

        self.box_icon_and_text.add_widget(self.box_image)
        self.box_icon_and_text.add_widget(self.status_label)

        self.status_card.add_widget(self.status_title)
        self.status_card.add_widget(Widget(size_hint_y=None, height="10dp"))
        self.status_card.add_widget(self.box_icon_and_text)

        # Lock Control Card 
        self.lock_card = MDCard(
            orientation="vertical",
            padding=20,
            radius=[15, 15, 15, 15],
            md_bg_color=(0.1, 0.1, 0.15, 1),
            size_hint=(0.5, 1)
        )
        self.lock_title = MDLabel(
            text="Lock Control",
            halign="center",
            font_style="H4",
            theme_text_color="Custom",
            text_color=(0.5, 0.7, 1, 1),
            size_hint_y=None,
            height="60dp",
            size_hint_x = None,
            width = "500dp",
            pos_hint = {"center_x": 0.5, "center_Y": 0.5}
        )

        self.lock_icon_and_text = MDBoxLayout(
            orientation="horizontal",
            spacing=10,
            size_hint=(None, None),
            width="180dp",
            height="60dp",
            pos_hint={"center_x": 0.5}
        )

        self.lock_image = Image(
            source="locked.png",
            size_hint=(None, None),
            size=("40dp", "40dp"),
            size_hint_y=None,
            height="60dp"
        )

        self.lock_status = MDLabel(
            text="Locked",
            font_style="H5",
            theme_text_color="Custom",
            text_color=(1, 0.4, 0.4, 1),
            valign="middle",
            size_hint=(1, 1)
        )

        self.lock_icon_and_text.add_widget(self.lock_image)
        self.lock_icon_and_text.add_widget(self.lock_status)

        self.btn_row = MDBoxLayout(
            orientation="horizontal",
            spacing=20,
            size_hint=(None, None),
            size=("300dp", "50dp"),
            size_hint_x = None,
            width = "90dp",
            pos_hint = {"center_x": 0.5, "center_Y": 0.5}
        )

        self.unlock_btn = MDRaisedButton(
            text="Unlock",
            font_size="25",
            md_bg_color=(0.2, 0.8, 0.2, 1),
            on_release=lambda x: self.send_command("unlock")
        )

        self.chat_button = MDRaisedButton(
            text="Chatbot",
            pos_hint={"center_x": 0.5},
            on_release=self.open_chatbot_dialog
        )
        self.add_widget(self.chat_button)


        self.btn_row.add_widget(self.unlock_btn)

        self.lock_card.add_widget(self.lock_title)
        self.lock_card.add_widget(Widget(size_hint_y=None, height="10dp"))
        self.lock_card.add_widget(self.lock_icon_and_text)
        self.lock_card.add_widget(Widget(size_hint_y=None, height="10dp"))
        self.lock_card.add_widget(self.btn_row)

        cards.add_widget(self.status_card)
        cards.add_widget(self.lock_card)
        self.add_widget(cards)

        #  Notification Section 
        self.notifications = []

        self.notification_card = MDCard(
            orientation="vertical",
            padding=20,
            radius=[15, 15, 15, 15],
            md_bg_color=(0.1, 0.1, 0.15, 1),
            size_hint=(1, 1)
        )
        notif_top = MDBoxLayout(orientation="horizontal", size_hint_y=None, height="30dp")
        notif_title = MDLabel(
            text="Recent Notifications",
            font_style="Subtitle2",
            theme_text_color="Custom",
            text_color=(0.5, 0.7, 1, 1)
        )
        self.clear_button = MDRaisedButton(
            text="Clear",
            md_bg_color=(0.5, 0.1, 0.1, 1),
            font_size="12sp",
            on_release=self.clear_notifications,
            size_hint=(None, None),
            height="28dp",
            width="80dp",
            pos_hint={"center_y": 0.5}
        )
        notif_top.add_widget(notif_title)
        notif_top.add_widget(Widget())  # Spacer
        notif_top.add_widget(self.clear_button)

        self.scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False  # Only vertical scrolling
        )

        self.notif_container = MDBoxLayout(
            orientation="vertical",
            spacing=8,
            padding=[5, 10],
            size_hint_y=None
        )
        self.notif_container.bind(minimum_height=self.notif_container.setter('height'))
        self.scroll.add_widget(self.notif_container)

        self.notification_card.add_widget(notif_top)
        self.notification_card.add_widget(self.scroll)
        self.add_widget(self.notification_card)

        # Firebase variables
        self.last_lock_status = ""
        self.last_package_status = ""
        self.vibration_counter = 0
        self.vibration_last_time = 0

        # Start checking Firebase regularly
        Clock.schedule_interval(self.safe_check_status, 5)
    def safe_check_status(self, dt):
        threading.Thread(target=self._check_status_thread).start()

    def clear_notifications(self, *args):
        self.notifications.clear()
        self.notif_container.clear_widgets()

    def _check_status_thread(self):
        try:
            data = db.child("guardbox").get().val()
            if data:
                Clock.schedule_once(lambda dt: self.update_status(data))
        except Exception as e:
            print("Firebase error:", e)
    
    def add_notification(self, message, icon_path):
        if len(self.notifications) >= 5:
            self.notifications.pop(0)
            self.notif_container.clear_widgets()
    
        self.notifications.append((message, icon_path))
    
        notif_row = MDBoxLayout(
            orientation="horizontal",
            spacing=10,
            size_hint_y=None,
            height="40dp",
            padding=[5, 5],
        )
    
        notif_icon = Image(
            source=icon_path,
            size_hint=(None, None),
            size=("30dp", "30dp"),
        )
    
        notif_text = MDLabel(
            text=message,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="Body1",
            halign="left",
            valign="middle",
        )
    
        notif_row.add_widget(notif_icon)
        notif_row.add_widget(notif_text)
    
        self.notif_container.add_widget(notif_row)
    

    def update_status(self, data):
        locked = data.get("locked", False)
        weight = data.get("weight", 0)
        vibration = data.get("vibration", False)

        lock_text = "Locked" if locked else "Unlocked"
        package_text = "Package Detected" if weight >= WEIGHT_THRESHOLD else "Box Empty"

        # Update Lock Status 
        if lock_text != self.last_lock_status:
            self.last_lock_status = lock_text
            icon = "locked.png" if locked else "unlocked.png"
            self.add_notification("GuardBox Locked" if locked else "GuardBox Unlocked", icon)

            if locked:
                self.show_locked()
            else:
                self.show_unlocked()

            self.lock_status.text = lock_text
            self.lock_image.source = icon

            if locked:
                self.lock_status.text_color = (1, 0.4, 0.4, 1)  # Red
            else:
                self.lock_status.text_color = (0.1, 1, 0.1, 1)  # Green

        #  Update Package Status 
        if package_text != self.last_package_status:
            self.last_package_status = package_text

            if weight >= WEIGHT_THRESHOLD:
                self.add_notification("Package detected", "box.png")
                self.show_cargo_true()
            else:
                self.add_notification("No package detected", "box.png")
                self.show_cargo_false()

            self.status_label.text = package_text
        #  Vibration Detection and Alerts 
        now = time.time()
        if vibration:
            if now - self.vibration_last_time > 10:
                self.vibration_counter = 0  # reset counter if time gap too big

            self.vibration_counter += 1
            self.vibration_last_time = now

            if self.vibration_counter < 3:
                self.add_notification("Vibration detected!", "alert.png")
                self.show_vibration_alert()
            elif self.vibration_counter == 3:
                self.add_notification("Multiple vibrations detected! Possible tampering!", "alert.png")
                self.show_special_vibration_alert()
    def show_vibration_alert(self):
        notification.notify(
            title="🚨 GuardBox Alert 🚨",
            message="Vibration detected!",
            timeout=5
        )

    def show_special_vibration_alert(self):
        notification.notify(
            title="🚨🚨🚨 GuardBox Critical Alert 🚨🚨🚨",
            message="Multiple vibrations detected! Immediate check recommended!",
            timeout=7
        )

    def show_cargo_true(self):
        notification.notify(
            title="📦 Package placed.",
            message="Your package has been placed inside the GuardBox.",
            timeout=5
        )

    def show_cargo_false(self):
        notification.notify(
            title="📦 Package is taken.",
            message="The GuardBox is now empty.",
            timeout=5
        )

    def show_locked(self):
        notification.notify(
            title="🔒 GuardBox Locked",
            message="The GuardBox has been securely locked.",
            timeout=5
        )

    def show_unlocked(self):
        notification.notify(
            title="🔓 GuardBox Unlocked",
            message="The GuardBox has been unlocked.",
            timeout=5
        )
    def send_command(self, cmd):
        def run():
            try:
                if cmd == "lock":
                    db.child("guardbox").update({"locked": True})
                else:
                    db.child("guardbox").update({"locked": False})
                # After sending a command, refresh status
                Clock.schedule_once(lambda dt: self.safe_check_status(0))
            except Exception as e:
                print("Command error:", e)

        threading.Thread(target=run).start()

    def open_chatbot_dialog(self, *args):
        if not hasattr(self, 'chat_dialog'):
            self.chat_input = MDTextField(
                hint_text="Ask something...",
                multiline=False
            )
    
            self.chat_dialog = MDDialog(
                title="GuardBox Chatbot",
                type="custom",
                content_cls=self.chat_input,
                buttons=[
                    MDFlatButton(
                        text="SEND",
                        on_release=self.send_chat_message
                    ),
                    MDFlatButton(
                        text="CLOSE",
                        on_release=lambda x: self.chat_dialog.dismiss()
                    ),
                ]
            )
        self.chat_dialog.open()


    def send_chat_message(self, *args):
        user_message = self.chat_input.text
        if user_message.strip():
            response = get_response(user_message)  # imported from chatbot.py
            self.chat_dialog.title = f"GuardBox Chatbot\n\nBot: {response}"
            self.chat_input.text = ""


class GuardBoxApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        return MainScreen()


if __name__ == '__main__':
    GuardBoxApp().run()