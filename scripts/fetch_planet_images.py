from __future__ import annotations

from pathlib import Path
from urllib.request import urlretrieve

from orbit_sim.planet_assets import PLANET_TEXTURE_SOURCES


def main() -> None:
    output_dir = Path("assets/planets")
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, config in PLANET_TEXTURE_SOURCES.items():
        output_path = output_dir / config["filename"]
        if output_path.exists():
            print(f"skip {name}: {output_path.name}")
            continue

        print(f"fetch {name}: {config['url']}")
        urlretrieve(config["url"], output_path)


if __name__ == "__main__":
    main()
