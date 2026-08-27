// Service Worker for Meridian Calendar Web Push Notifications

self.addEventListener('push', function(event) {
  if (event.data) {
    try {
      const payload = event.data.json();
      const options = {
        body: payload.body || 'Upcoming event reminder',
        icon: payload.icon || '/calendar-icon.svg',
        badge: payload.badge || '/calendar-icon.svg',
        data: {
          url: payload.url || '/'
        },
        actions: [
          { action: 'open', title: 'Open Event' },
          { action: 'close', title: 'Dismiss' }
        ]
      };

      event.waitUntil(
        self.registration.showNotification(payload.title || 'Meridian Calendar', options)
      );
    } catch (e) {
      console.warn('Error parsing push data:', e);
    }
  }
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();

  if (event.action === 'close') {
    return;
  }

  const targetUrl = event.notification.data?.url || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
      for (let i = 0; i < clientList.length; i++) {
        const client = clientList[i];
        if (client.url === targetUrl && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
