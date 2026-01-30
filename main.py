#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# main.py - Thin wrapper for AudioWave
# Calls the real entry point: audiowave.py

import sys
from audiowave import main as audiowave_main


def main():
    audiowave_main()


if __name__ == "__main__":
    main()
