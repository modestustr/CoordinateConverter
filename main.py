# main.py
import argparse
import os
import subprocess
import sys

from config.logging import configure_logging
from core.coord import CoordConverter
from core.input_resolver import InputResolver


def configure_console_encoding():
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8")
            except Exception:
                continue


def run_ui():
    """Launch the Streamlit UI."""
    try:
        from streamlit.runtime import exists

        if exists():
            return
    except ImportError:
        pass

    print("🚀 Arayüz başlatılıyor...")
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "streamlit_app.py"],
        env=env,
    )


def main():
    configure_console_encoding()
    configure_logging()

    parser = argparse.ArgumentParser(
        description="Coordinate Converter - Merkezi Giriş Noktası"
    )

    parser.add_argument(
        "coords", type=str, nargs="?", help="Giriş koordinatları (Örn: '39.93,32.85')"
    )
    parser.add_argument("--src", help="Kaynak CRS")
    parser.add_argument("--tgt", help="Hedef CRS")
    parser.add_argument("--ui", action="store_true", help="Streamlit arayüzünü başlat")

    args = parser.parse_args()

    if args.ui or not args.coords:
        run_ui()
        return

    engine = CoordConverter()
    resolver = InputResolver()

    try:
        details = resolver.resolve(args.coords)
        if not details["is_valid"]:
            print(f"ERROR: {details['suggestion']['reason']}")
            return

        x, y = details["x"], details["y"]
        rx, ry, _ = engine.transform_point(x, y, args.src, args.tgt)
        meta = engine.get_transformer_info(args.src, args.tgt, x, y)

        print("\n=== RESULT ===")
        print(f"Input : {y}, {x}")
        print(f"Output: {ry:.6f}, {rx:.6f}")
        print(f"Method: {meta['description']}")

    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
