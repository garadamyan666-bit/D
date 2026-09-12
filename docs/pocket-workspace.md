# Pocket Option screenshot workspace

ACTIVE_WORKSPACE=POCKET_OPTION is now the default. It selects the screenshot
homepage and blocks all Binance network requests, scans, and verification.
No Binance subscriptions, forecasts, users or history are deleted. Setting
ACTIVE_WORKSPACE=BINANCE and restarting restores the previous workspace.

There is no direct Pocket Option quote feed or order execution. Users provide
the chart, symbol, OTC/regular label, candle interval and intended expiry.
Expiry and candle interval remain separate. Never verify Pocket Option or
OTC screenshots against Binance quotes. Admin currently shows the preserved
Binance evaluation only; it is NOT a Pocket Option accuracy dashboard.

Image review requires a server-side GEMINI_API_KEY and access to the configured
GEMINI_VISION_MODEL. Key presence is not proof of billing/model availability.
No key is embedded in frontend assets or requested in chat. The form discloses
image transfer to Google Gemini and requires consent; crop names, balances and other
personal information first. Images and answers are not persisted by this app.
`store:false` requests disabled API logging; it does not override Google's
free-tier data-use policy. Free-tier content may be used to improve products.
There is no fallback to OpenAI or any other paid provider. Free eligibility
depends on the Google project/model quota; this app cannot set the billing
tier. Keep the Google project on Free Tier. Default model: gemini-3.8-flash.

The review is a short visual explanation, not a timed entry signal. It avoids
invented confidence probabilities and flags unreadable charts or contradictory
labels. There is no demonstrated accuracy improvement without a separately
collected, prospective Pocket Option dataset and fixed expiry outcomes.

Still unavailable: live Pocket quotes, screenshot-triggered Telegram alerts,
automatic screenshot outcome verification. Do not imply these are connected.
