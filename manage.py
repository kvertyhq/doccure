#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "doccure.settings")
    
    # Load .env file if it exists so NGROK_AUTHTOKEN and other vars are available early
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parent
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

    # Start ngrok tunnel if running the dev server
    if len(sys.argv) > 1 and sys.argv[1] == "runserver" and os.environ.get("RUN_MAIN") != "true":
        port = 8000
        for arg in sys.argv[2:]:
            if ":" in arg:
                try:
                    port = int(arg.split(":")[-1])
                except ValueError:
                    pass
            elif arg.isdigit():
                port = int(arg)
        
        try:
            import ngrok
            authtoken = os.environ.get("NGROK_AUTHTOKEN")
            if authtoken:
                listener = ngrok.forward(port, authtoken=authtoken)
            else:
                listener = ngrok.forward(port)
            print(f"\n[ngrok] Tunnel established! Public URL: {listener.url()}\n")
        except Exception as e:
            print(f"\n[ngrok] Failed to start tunnel: {e}\n")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
