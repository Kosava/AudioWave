#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt6.QtCore import QSharedMemory

APP_ID = "audiowave_single_instance"


def main():
    # 🔒 SINGLE INSTANCE CHECK
    shared_memory = QSharedMemory(APP_ID)
    if not shared_memory.create(1):
        # Već postoji instanca → samo izađi
        sys.exit(0)

    # 🚀 Pokreni aplikaciju (ona sama pravi QApplication)
    from audiowave.main import main as audiowave_main
    audiowave_main()


if __name__ == "__main__":
    main()
