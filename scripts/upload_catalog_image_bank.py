"""Carga a Cloudinary el banco curado de imágenes de referencia del catálogo.

Las credenciales se leen de ``backend/.env`` y nunca se escriben en el CSV ni
en la salida. El manifiesto de entrada conserva la procedencia y licencia de
cada imagen. Los identificadores estables permiten repetir una carga sin crear
recursos duplicados.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT_DIR / "data" / "catalog" / "unsplash_image_sources.csv"
DEFAULT_OUTPUT = ROOT_DIR / "output" / "cloudinary_catalog_uploads.csv"
ENV_FILE = ROOT_DIR / "backend" / ".env"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"'))


def required_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Falta {name} en backend/.env.")
    return value


def cloudinary_signature(params: dict[str, str], api_secret: str) -> str:
    payload = "&".join(f"{key}={params[key]}" for key in sorted(params))
    return hashlib.sha1(f"{payload}{api_secret}".encode()).hexdigest()


def encode_multipart(fields: dict[str, str], file_bytes: bytes, filename: str, mime_type: str) -> tuple[bytes, str]:
    boundary = f"----MuebleriaIvan{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for key, value in fields.items():
        chunks.extend(
            (
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(),
                value.encode(),
                b"\r\n",
            )
        )
    chunks.extend(
        (
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode(),
            f"Content-Type: {mime_type}\r\n\r\n".encode(),
            file_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        )
    )
    return b"".join(chunks), boundary


def download_image(url: str) -> tuple[bytes, str]:
    request = Request(url, headers={"User-Agent": "Muebleria-Ivan-Academic-Catalog/1.0"})
    with urlopen(request, timeout=45) as response:  # nosec B310: URLs are curated in the repository.
        mime_type = response.headers.get_content_type()
        return response.read(), mime_type if mime_type.startswith("image/") else "image/jpeg"


def upload_image(row: dict[str, str], credentials: dict[str, str]) -> dict[str, str | int]:
    file_bytes, mime_type = download_image(row["source_url"])
    timestamp = str(int(datetime.now(UTC).timestamp()))
    public_id = f"muebleria-ivan/products/{row['product_slug']}/{row['image_id']}"
    signed_params = {"overwrite": "true", "public_id": public_id, "timestamp": timestamp}
    fields = {
        **signed_params,
        "api_key": credentials["api_key"],
        "signature": cloudinary_signature(signed_params, credentials["api_secret"]),
    }
    payload, boundary = encode_multipart(
        fields,
        file_bytes,
        f"{row['image_id']}.jpg",
        mime_type,
    )
    endpoint = f"https://api.cloudinary.com/v1_1/{credentials['cloud_name']}/image/upload"
    request = Request(
        endpoint,
        data=payload,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urlopen(request, timeout=90) as response:  # nosec B310: endpoint is derived from local config.
        uploaded = json.loads(response.read().decode("utf-8"))
    return {
        **row,
        "cloudinary_public_id": uploaded["public_id"],
        "secure_url": uploaded["secure_url"],
        "width": uploaded["width"],
        "height": uploaded["height"],
        "uploaded_at": datetime.now(UTC).isoformat(),
    }


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    required_columns = {
        "product_slug",
        "image_id",
        "source_url",
        "source_page_url",
        "source_author",
        "source_license_url",
        "alt_text",
        "display_order",
    }
    missing = required_columns - set(rows[0] if rows else ())
    if missing:
        raise RuntimeError(f"El manifiesto no contiene: {', '.join(sorted(missing))}.")
    return rows


def write_results(path: Path, rows: list[dict[str, str | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "product_slug",
        "image_id",
        "display_order",
        "cloudinary_public_id",
        "secure_url",
        "width",
        "height",
        "alt_text",
        "source_page_url",
        "source_author",
        "source_license_url",
        "uploaded_at",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true", help="Valida el manifiesto sin subir archivos.")
    parser.add_argument("--limit", type=int, help="Cantidad máxima de imágenes a procesar.")
    args = parser.parse_args()

    rows = read_manifest(args.manifest)
    if args.limit is not None:
        rows = rows[: args.limit]
    if args.dry_run:
        print(f"Manifiesto válido: {len(rows)} imágenes listas para cargar.")
        return

    load_dotenv(ENV_FILE)
    credentials = {
        "cloud_name": required_setting("MUEBLERIA_CLOUDINARY_CLOUD_NAME"),
        "api_key": required_setting("MUEBLERIA_CLOUDINARY_API_KEY"),
        "api_secret": required_setting("MUEBLERIA_CLOUDINARY_API_SECRET"),
    }
    results: list[dict[str, str | int]] = []
    for index, row in enumerate(rows, start=1):
        try:
            result = upload_image(row, credentials)
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
            write_results(args.output, results)
            raise RuntimeError(f"No se pudo cargar {row['image_id']}: {error}") from error
        results.append(result)
        write_results(args.output, results)
        print(f"[{index}/{len(rows)}] {row['product_slug']}: {result['secure_url']}")
    print(f"Carga terminada: {len(results)} imágenes. Resultado: {args.output}")


if __name__ == "__main__":
    main()
