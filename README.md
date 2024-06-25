# SChwab Python API & Streamer
Handles Authentication, WebSocket streaming subscriptions and API requests.
(Developed on Anaconda Spyder on Apple platform)

### Auth:
    Handles the authentication process and keeps a valid access token to be used
    by Schwab (endpoint requests).
    To authenticate, you need to provide:
        "user": -- Used to generate the refresh token file
        "redirect_uri": "https://127.0.0.1",
        "client_id": str -- Apps credential from https://developer.schwab.com/
        "app_secret": str -- Apps credential from https://developer.schwab.com/

### API:
    Handles all API requests. GET, POST,PUT, PATCH.

    TODO:
       - Implement Enumerate.
       - Implement ASYNC.

### Websoket:
    Handles  Websocket connection:
             - Login
             - Subscription request
             - Reestablish connection with all subscriptions back automatically.

    TODO:
     - Implement ASYNC.

### Streamer:
    Provides one method for each kind of subscription with the proper documentation
    and default values set.


### Balances:
    Downloads the complete transactions history and provides P/L
    for each Day/Week/Month/Year with FIFO and LIFO approaches.


### Test:
    Examples on each API endpoint and working streamer subscriptions


#### Next Steps:

- Desktop App
- Trading Bot
- AI trading Bot
- AI portfolio

### Project Dependencies
```mermaid
graph TD;
    Service-->API;
    Service-->Streamer;
    API-->Auth;
    Streamer-->WebSocket;
    WebSocket-->API;
