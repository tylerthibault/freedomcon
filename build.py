"""build.py — pre-deploy build step.

Run automatically during the nixpacks build phase (see nixpacks.toml).
Converts all PNG/JPG images in src/static/img/ to optimized WebP files.
"""
import subprocess
import sys


def run_image_optimization() -> None:
    print("[build] Running image optimization...")
    result = subprocess.run(
        [sys.executable, "optimize_images.py"],
        check=False,
    )
    if result.returncode != 0:
        # Non-fatal: log the failure but don't abort the build
        print("[build] WARNING: Image optimization finished with errors (non-fatal).")
    else:
        print("[build] Image optimization complete.")


if __name__ == "__main__":
    run_image_optimization()
