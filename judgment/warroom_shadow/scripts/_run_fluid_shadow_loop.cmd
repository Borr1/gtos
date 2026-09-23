@echo off
set GTOS_JEV_FLUID_GATES_SHADOW=1
set GTOS_JEV_FLUID_GATES_APPLY=0
set GTOS_JEV_FLUID_GATES_LOG_DIR=host-local\redacted_host\repo\judgment\live\jev_sidecar
set PYTHONPATH=host-local\redacted_host\repo\judgment\warroom_shadow
cd /d host-local\redacted_host\repo\judgment\warroom_shadow
host-local\redacted_host\repo\.venv\Scripts\python.exe scripts\run_jev_fluid_gates_shadow.py
