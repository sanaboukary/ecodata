#!/bin/bash
cd "e:/DISQUE C/Desktop/Implementation plateforme" || exit 1
./.venv/Scripts/python.exe analyse_ia_simple.py && \
./.venv/Scripts/python.exe decision_finale_brvm.py && \
./.venv/Scripts/python.exe top5_engine_brvm.py
