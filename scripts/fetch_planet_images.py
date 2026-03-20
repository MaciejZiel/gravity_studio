from __future__ import annotations

import argparse
from pathlib import Path
import sys
from urllib.request import urlretrieve

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from orbit_sim.planet_assets import PLANET_TEXTURE_SOURCES


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    output_dir = Path("assets/planets")
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, config in PLANET_TEXTURE_SOURCES.items():
        output_path = output_dir / config["filename"]
        if output_path.exists() and not args.refresh:
            print(f"skip {name}: {output_path.name}")
            continue

        print(f"fetch {name}: {config['url']}")
        urlretrieve(config["url"], output_path)


if __name__ == "__main__":
    main()
