import argparse
import json
import os
from pathlib import Path

import requests


def print_json(title, data):
    print(f"\n=== {title} ===")
    print(json.dumps(data, ensure_ascii=False, indent=2)[:8000])


def test_http(base_url: str, image_path: Path, timeout: int):
    health_url = f"{base_url.rstrip('/')}/health"
    ocr_url = f"{base_url.rstrip('/')}/ocr"

    health = requests.get(health_url, timeout=timeout)
    print(f"\nGET {health_url} -> {health.status_code}")
    try:
        print_json("health", health.json())
    except Exception:
        print(health.text[:4000])

    with image_path.open("rb") as f:
        resp = requests.post(
            ocr_url,
            files={"file": (image_path.name, f, "image/png")},
            timeout=timeout,
        )

    print(f"\nPOST {ocr_url} -> {resp.status_code}")
    try:
        payload = resp.json()
        print_json("ocr response", payload)
        results = payload.get("results") or []
        texts = [
            region.get("text")
            for page in results
            for region in (page.get("text_regions") or [])
            if region.get("text")
        ]
        print(f"\nrecognized_text_count={len(texts)}")
        for text in texts[:20]:
            print(f"- {text}")
    except Exception:
        print(resp.text[:8000])


def test_local(image_path: Path):
    # Set before importing paddle / paddleocr. This is useful for checking whether
    # the CPU oneDNN path is causing runtime failures in the current environment.
    os.environ.setdefault("FLAGS_use_mkldnn", "0")
    os.environ.setdefault("FLAGS_enable_pir_api", "0")

    from paddleocr import PaddleOCR

    print("\n=== local PaddleOCR ===")
    ocr = PaddleOCR(
        lang=os.getenv("OCR_LANG", "ch"),
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        device=os.getenv("DOC_LAYOUT_DEVICE", "cpu"),
    )

    if hasattr(ocr, "predict"):
        result = ocr.predict(str(image_path))
    else:
        result = ocr.ocr(str(image_path), cls=False)

    print(f"result_type={type(result).__name__}")
    print(str(result)[:8000])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--image", default=str(Path(__file__).with_name("test.png")))
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--local", action="store_true")
    args = parser.parse_args()

    image_path = Path(args.image).resolve()
    if not image_path.exists():
        raise FileNotFoundError(image_path)

    print(f"image={image_path}")
    test_http(args.base_url, image_path, args.timeout)

    if args.local:
        test_local(image_path)


if __name__ == "__main__":
    main()
