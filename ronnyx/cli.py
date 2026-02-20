import argparse
import os
from typing import Optional

import requests

DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/chat"
DEFAULT_SESSION_ID = "1"


def chat_loop(base_url: str, session_id: str) -> None:
    """
    Simple interactive chat loop over the HTTP API.
    """
    print(f"Connected to {base_url} (session: {session_id})")
    print("Type 'exit' or 'quit' to leave.\n")

    while True:
        try:
            message = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not message:
            continue

        if message.lower() in {"exit", "quit"}:
            break

        try:
            response = requests.post(
                base_url,
                json={"session_id": session_id, "message": message},
                timeout=120,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"[error] request failed: {exc}")
            continue

        try:
            payload = response.json()
        except ValueError:
            print("[error] response is not valid JSON")
            continue

        reply: Optional[str] = payload.get("reply")
        if reply is None:
            print("[warning] no 'reply' field in response")
        else:
            print(f"Ronnyx > {reply}")

    print("Exiting.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ronnyx terminal client",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("RONNYX_BASE_URL", DEFAULT_BASE_URL),
        help=(
            "Chat API base URL. "
            "Defaults to RONNYX_BASE_URL env var or "
            f"{DEFAULT_BASE_URL!r} if not set."
        ),
    )
    parser.add_argument(
        "--session-id",
        default=os.getenv("RONNYX_SESSION_ID", DEFAULT_SESSION_ID),
        help=(
            "Session identifier used to maintain conversation context. "
            "Defaults to RONNYX_SESSION_ID env var or "
            f"{DEFAULT_SESSION_ID!r}."
        ),
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    chat_loop(base_url=args.base_url, session_id=args.session_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
