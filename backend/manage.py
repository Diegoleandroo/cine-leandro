#!/usr/bin/env python
"""Ferramenta de linha de comando do Django (migrate, runserver, disparar_avisos...)."""
import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cinema.frameworks_drivers.django_projeto.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
