import os
import requests

from app.config import settings

HEADERS = {"ngrok-skip-browser-warning": "1"}


def alive(timeout=3):
    if not settings.colab_url:
        return False

    try:
        return requests.get(
            f"{settings.colab_url}/health",
            headers=HEADERS,
            timeout=timeout
        ).ok
    except requests.RequestException:
        return False


def _post(path, payload):
    r = requests.post(
        f"{settings.colab_url}{path}",
        json=payload,
        headers=HEADERS,
        timeout=420
    )
    r.raise_for_status()
    return {**r.json(), "engine": "colab"}


def directions(payload):
    return _post("/directions", payload)


def content(payload):
    return _post("/content", payload)


def image(payload):
    try:
        return _post("/image", payload)

    except Exception as colab_error:
        from google import genai
        from google.genai import types

        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise colab_error

        client = genai.Client(api_key=api_key)

        prompt = (
            "Create a professional advertising photograph for a marketing campaign. "
            f"Product: {payload.get('product_name', '')}. "
            f"Description: {payload.get('product_description', '')}. "
            f"Visual concept: {payload.get('visual_concept', '')}. "
            "Photorealistic, premium commercial photography, no text."
        )

        contents = [prompt]

        product_photo = payload.get("product_photo")
        if product_photo:
            import base64

            header, encoded = product_photo.split(",", 1)
            image_bytes = base64.b64decode(encoded)

            mime_type = header.split(";")[0].replace("data:", "")

            contents.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type
                )
            )

            contents[0] = (
                prompt
                + " Preserve the exact identity, shape, colors and packaging "
                  "of the uploaded product. Create a new advertising photoshoot "
                  "around the same product."
            )

        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"]
            ),
        )

        for part in response.candidates[0].content.parts:
            if getattr(part, "inline_data", None):
                image_bytes = part.inline_data.data
                image_b64 = base64.b64encode(image_bytes).decode()

                mime = part.inline_data.mime_type or "image/png"

                return {
                    "image": f"data:{mime};base64,{image_b64}",
                    "prompt": prompt,
                    "mode": "gemini_fallback",
                    "engine": "gemini",
                }

        raise RuntimeError(
            f"Colab image generation failed: {colab_error}; "
            "Gemini did not return an image."
        )