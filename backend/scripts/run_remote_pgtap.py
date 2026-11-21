"""Run the repository pgTAP files against the configured PostgreSQL database.

Every test file owns a transaction and ends with ROLLBACK, so no fixture or
assertion data remains in the target database.
"""

from pathlib import Path

import psycopg

from app.core.config import Settings

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TEST_DIRECTORY = REPOSITORY_ROOT / "supabase" / "tests" / "database"


def main() -> None:
    database_url = Settings().database_url
    if not database_url:
        raise SystemExit("MUEBLERIA_DATABASE_URL no está configurada.")
    conninfo = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    failures: list[str] = []
    total_checks = 0

    with psycopg.connect(conninfo) as connection:
        for test_path in sorted(TEST_DIRECTORY.glob("*_test.sql")):
            checks: list[str] = []
            with connection.cursor() as cursor:
                cursor.execute(test_path.read_text(encoding="utf-8"), prepare=False)
                while True:
                    if cursor.description:
                        for row in cursor.fetchall():
                            if row and isinstance(row[0], str):
                                result = row[0]
                                if result.startswith(("ok ", "not ok ")):
                                    checks.append(result)
                                    if result.startswith("not ok "):
                                        failures.append(f"{test_path.name}: {result}")
                    if not cursor.nextset():
                        break
            total_checks += len(checks)
            print(f"{test_path.name}: {len(checks)} comprobaciones")

    if failures:
        raise SystemExit("\n".join(failures))
    print(f"pgTAP remoto aprobado: {total_checks} comprobaciones")


if __name__ == "__main__":
    main()
