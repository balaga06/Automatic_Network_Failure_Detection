from plyer import notification

def show_desktop_alert(title, message):
    notification.notify(
        title=title,
        message=message,
        timeout=5
    )