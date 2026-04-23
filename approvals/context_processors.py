from .models import Notification

def notifications(request):
    """
    Makes unread notifications and their counts available on every page.
    """
    if request.user.is_authenticated:
        unread_notifs = request.user.notifications.filter(is_read=False).select_related('user')
        return {
            'nav_notifications': unread_notifs[:10],
            'unread_notif_count': unread_notifs.count()
        }
    return {
        'nav_notifications': [],
        'unread_notif_count': 0
    }
