self.addEventListener('push', function (event) {
    let data = {};

    if (event.data) {
        try {
            data = event.data.json();
        } catch (error) {
            data = {
                title: 'DNMS Notification',
                body: event.data.text()
            };
        }
    }

    const title = data.title || 'DNMS Notification';

    const options = {
        body: data.body || data.message || 'A new college notification is available.',
        data: {
            url: data.url || '/notifications/'
        }
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();

    const targetUrl = event.notification.data?.url || '/notifications/';

    event.waitUntil(
        clients.matchAll({
            type: 'window',
            includeUncontrolled: true
        }).then(function (windowClients) {
            for (const client of windowClients) {
                if ('focus' in client) {
                    return client.navigate(targetUrl).then(function (focusedClient) {
                        return focusedClient || client.focus();
                    });
                }
            }

            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});
