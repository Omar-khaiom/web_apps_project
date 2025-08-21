// SmartRecipes Service Worker
// Version 1.0.0

const CACHE_NAME = 'smartrecipes-v1.0.0';
const OFFLINE_CACHE = 'smartrecipes-offline-v1.0.0';

// Files to cache for offline use
const STATIC_CACHE_FILES = [
  '/',
  '/input',
  '/static/style.css',
  '/static/manifest.json',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  // Add more static assets as needed
];

// Dynamic cache patterns
const API_CACHE_PATTERNS = [
  /\/recipe\/\d+/,
  /\/favorites/,
];

// Network-first cache strategy for API calls
const NETWORK_FIRST_PATTERNS = [
  /\/generate/,
  /\/toggle-favorite/,
  /\/login/,
  /\/register/,
];

// Install Service Worker
self.addEventListener('install', event => {
  console.log('🔧 Service Worker installing...');
  
  event.waitUntil(
    Promise.all([
      // Cache static files
      caches.open(CACHE_NAME).then(cache => {
        console.log('📦 Caching static files...');
        return cache.addAll(STATIC_CACHE_FILES.map(url => new Request(url, { cache: 'reload' })));
      }),
      // Create offline cache
      caches.open(OFFLINE_CACHE).then(cache => {
        console.log('💾 Creating offline cache...');
        return cache.put('/offline', new Response(`
          <!DOCTYPE html>
          <html>
          <head>
            <title>SmartRecipes - Offline</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
              body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
              .offline-container { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
              h1 { color: #4CAF50; margin-bottom: 20px; }
              .icon { font-size: 64px; margin-bottom: 20px; }
              p { color: #666; line-height: 1.5; }
              .retry-btn { background: #4CAF50; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; font-size: 16px; margin-top: 20px; }
              .retry-btn:hover { background: #45a049; }
            </style>
          </head>
          <body>
            <div class="offline-container">
              <div class="icon">🍳</div>
              <h1>You're Offline</h1>
              <p>SmartRecipes needs an internet connection to search for recipes. Check your connection and try again.</p>
              <p><strong>Available offline:</strong></p>
              <ul style="text-align: left; color: #666;">
                <li>Your saved favorites</li>
                <li>Search history</li>
                <li>Recipe browsing</li>
              </ul>
              <button class="retry-btn" onclick="window.location.reload()">Try Again</button>
            </div>
          </body>
          </html>
        `, { headers: { 'Content-Type': 'text/html' } }));
      })
    ]).then(() => {
      console.log('✅ Service Worker installed successfully');
      // Skip waiting to activate immediately
      return self.skipWaiting();
    })
  );
});

// Activate Service Worker
self.addEventListener('activate', event => {
  console.log('🚀 Service Worker activating...');
  
  event.waitUntil(
    Promise.all([
      // Clean up old caches
      caches.keys().then(cacheNames => {
        return Promise.all(
          cacheNames
            .filter(cacheName => cacheName !== CACHE_NAME && cacheName !== OFFLINE_CACHE)
            .map(cacheName => {
              console.log('🗑️ Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      }),
      // Claim all clients
      self.clients.claim()
    ]).then(() => {
      console.log('✅ Service Worker activated successfully');
    })
  );
});

// Fetch event handler
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  
  // Skip non-HTTP requests
  if (!request.url.startsWith('http')) {
    return;
  }
  
  // Handle different types of requests
  if (NETWORK_FIRST_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    // Network-first strategy for API calls
    event.respondWith(networkFirst(request));
  } else if (API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    // Cache-first strategy for cacheable content
    event.respondWith(cacheFirst(request));
  } else if (request.destination === 'image') {
    // Cache-first for images with fallback
    event.respondWith(cacheFirstWithFallback(request));
  } else {
    // Stale-while-revalidate for other requests
    event.respondWith(staleWhileRevalidate(request));
  }
});

// Network-first strategy
async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('📱 Network failed, trying cache for:', request.url);
    
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      const offlineResponse = await caches.match('/offline');
      if (offlineResponse) {
        return offlineResponse;
      }
    }
    
    throw error;
  }
}

// Cache-first strategy
async function cacheFirst(request) {
  const cachedResponse = await caches.match(request);
  
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('📱 Failed to fetch:', request.url);
    throw error;
  }
}

// Cache-first with fallback for images
async function cacheFirstWithFallback(request) {
  try {
    return await cacheFirst(request);
  } catch (error) {
    // Return a placeholder image for failed image requests
    return new Response(
      '<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#f0f0f0"/><text x="50%" y="50%" font-family="Arial" font-size="14" fill="#999" text-anchor="middle" dy=".3em">Image unavailable</text></svg>',
      { headers: { 'Content-Type': 'image/svg+xml' } }
    );
  }
}

// Stale-while-revalidate strategy
async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  const fetchPromise = fetch(request).then(networkResponse => {
    if (networkResponse.status === 200) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  }).catch(error => {
    console.log('📱 Network error for:', request.url, error);
    return cachedResponse;
  });
  
  return cachedResponse || fetchPromise;
}

// Background sync for offline actions
self.addEventListener('sync', event => {
  console.log('🔄 Background sync triggered:', event.tag);
  
  if (event.tag === 'favorite-sync') {
    event.waitUntil(syncFavorites());
  }
});

// Sync favorites when back online
async function syncFavorites() {
  try {
    // Get pending favorite actions from IndexedDB
    // This would require implementing IndexedDB storage
    console.log('🔄 Syncing favorites...');
    // Implementation would go here
  } catch (error) {
    console.error('❌ Favorite sync failed:', error);
  }
}

// Handle push notifications (future feature)
self.addEventListener('push', event => {
  if (!event.data) return;
  
  const data = event.data.json();
  
  const options = {
    body: data.body || 'New recipe suggestions available!',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-96x96.png',
    data: data,
    actions: [
      {
        action: 'view',
        title: 'View Recipes'
      },
      {
        action: 'dismiss',
        title: 'Dismiss'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'SmartRecipes', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/input')
    );
  }
});

console.log('📱 SmartRecipes Service Worker loaded successfully!');
