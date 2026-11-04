# Google Maps setup

1. Create or select a Google Cloud project and enable billing.
2. Enable Maps JavaScript API. Enable Places API (New) if/when autocomplete is activated in the UI.
3. Create a browser key restricted by HTTP referrers to localhost and your production domain. Add it as `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`.
4. Restrict the key to the required APIs. Never use a server-only unrestricted key in the browser.
5. For server-side Google APIs, use a separate secret `GOOGLE_MAPS_SERVER_KEY` on the backend and restrict it by server IP/API.

The property detail map displays a graceful configuration fallback until coordinates and a valid key are available. Property latitude/longitude fields are persisted by the API.
