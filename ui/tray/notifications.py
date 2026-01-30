# ui/tray/notifications.py

class TrayNotifications:
    """Helper za tray notifikacije"""

    def __init__(self, tray_icon):
        self.tray_icon = tray_icon

    def now_playing(self, title, artist=""):
        if artist:
            message = f"{artist} - {title}"
        else:
            message = title

        self.tray_icon.show_message("Now Playing", message)

    def paused(self):
        self.tray_icon.show_message("AudioWave", "Playback paused")

    def resumed(self):
        self.tray_icon.show_message("AudioWave", "Playback resumed")

    def stopped(self):
        self.tray_icon.show_message("AudioWave", "Playback stopped")

    def running_in_tray(self):
        self.tray_icon.show_message("AudioWave", "Still running in tray")
