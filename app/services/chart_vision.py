"""Ephemeral AI review of a user-provided trading-chart screenshot."""
from __future__ import annotations

import base64
import re

import requests

from app.config import settings

DATA_URL = re.compile(r"^data:(image/(?:png|jpeg|webp));base64,([A-Za-z0-9+/=]+)$")
MAX_IMAGE_BYTES = 5 * 1024 * 1024


class ChartVisionError(RuntimeError):
    pass


def validate_image(data_url: str) -> str:
    match = DATA_URL.fullmatch(data_url)
    if not match:
        raise ValueError("Ընտրեք PNG, JPG կամ WEBP նկար։")
    try:
        size = len(base64.b64decode(match.group(2), validate=True))
    except ValueError as exc:
        raise ValueError("Նկարը վնասված է կամ սխալ ձևաչափ ունի։") from exc
    if size < 1_000:
        raise ValueError("Նկարը չափազանց փոքր է։")
    if size > MAX_IMAGE_BYTES:
        raise ValueError("Նկարի առավելագույն չափը 5 MB է։")
    return data_url


def analyze_chart(data_url: str, symbol: str, timeframe: str) -> str:
    if not settings.openai_api_key:
        raise ChartVisionError("Տեսողական AI-ը դեռ միացված չէ․ անհրաժեշտ է OPENAI_API_KEY։")
    image = validate_image(data_url)
    prompt = f"""Դու շուկայական գրաֆիկի զգույշ վերլուծող ես։ Պատասխանիր միայն հայերենով։
Օգտատերը նշել է {symbol or 'չնշված շուկա'} և {timeframe or 'չնշված ժամանակահատված'}։
Վերլուծիր միայն նկարում հստակ տեսանելի փակված մոմերը և ցուցիչները։ Մի հորինիր չերևացող գին կամ տվյալ։
Տուր կարճ, պարզ պատասխան այս կառուցվածքով.
Միտում՝ աճող / նվազող / չեզոք
Կարևոր աջակցություն՝ ...
Կարևոր դիմադրություն՝ ...
Աճի սցենար՝ ...
Անկման սցենար՝ ...
Անվավերացման մակարդակ՝ ...
Եզրակացություն՝ BUY / SELL / WAIT
Վստահություն՝ 0-100% (սա տեսողական գնահատական է, ոչ իրական հավանականություն)
Վերջում մեկ նախադասությամբ նշիր, որ screenshot-ը միայնակ բավարար չէ գործարքի համար։"""
    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"},
            json={
                "model": settings.openai_vision_model,
                "store": False,
                "input": [{"role": "user", "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": image, "detail": "high"},
                ]}],
            },
            timeout=75,
        )
        response.raise_for_status()
        payload = response.json()
        chunks = [part.get("text", "") for item in payload.get("output", [])
                  for part in item.get("content", []) if part.get("type") == "output_text"]
        text = "\n".join(chunk for chunk in chunks if chunk).strip()
        if not text:
            raise ChartVisionError("AI-ից պատասխան չստացվեց։")
        return text
    except requests.RequestException as exc:
        status = getattr(exc.response, "status_code", None)
        if status == 401:
            raise ChartVisionError("OpenAI API key-ը սխալ է կամ անվավեր։") from None
        if status == 429:
            raise ChartVisionError("OpenAI սահմանաչափը սպառվել է․ ստուգեք API billing-ը։") from None
        raise ChartVisionError("Տեսողական AI ծառայությունը ժամանակավորապես անհասանելի է։") from None
