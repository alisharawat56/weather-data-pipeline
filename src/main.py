
"""Run the complete weather data pipeline."""

import logging
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "pipeline.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)


def run_step(description, script_name):
    """Run a pipeline script and stop if it fails."""
    script_path = PROJECT_ROOT / "src" / script_name

    logger.info("Starting step: %s", description)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Step failed: {description} (exit code {result.returncode})"
        )

    logger.info("Completed step: %s", description)


def main():
    logger.info("Weather pipeline started.")

    try:
        # Fetch all three cities, clean the data, and save the CSV.
        run_step(
            "Fetch and clean weather data",
            "clean_weather.py",
        )

        # Load cleaned observations into PostgreSQL.
        run_step(
            "Load weather data into PostgreSQL",
            "load_weather.py",
        )

        # Fill wind speeds for existing observations where missing.
        run_step(
            "Update missing wind speeds",
            "update_wind_speed.py",
        )

        logger.info("Weather pipeline completed successfully.")

    except Exception:
        logger.exception("Weather pipeline failed.")
        raise


if __name__ == "__main__":
    main()
