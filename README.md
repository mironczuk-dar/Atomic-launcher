# Atomic Launcher - Developer Documentation

**Version:** 1.0 (Alpha)

**Repository:** [mironczuk-dar/Atomic-launcher](https://github.com/mironczuk-dar/Atomic-launcher)

> This developer guide is intended for contributors and maintainers who want to understand how Atomic Launcher starts, how the project is organized, and how to get a development environment running on Windows or Linux.

---

## Table of Contents

1. Introduction
2. Quick Start
   - Windows
   - Linux
3. Project Structure
4. Core Architecture
5. Running the Launcher
6. Dependencies
7. Adding or Inspecting Games
8. Contribution Workflow
9. Notes for Raspberry Pi and GPIO

---

## 1. Introduction

Atomic Launcher is a Pygame-based launcher designed to host, browse, and run a collection of games from a unified interface. The project is organized to separate platform setup, UI state flow, asset loading, and game installation logic into distinct modules.

This document replaces the older documentation and reflects the actual current repository structure and startup process.

---

## 2. Quick Start

Atomic Launcher provides dedicated startup scripts for both Windows and Linux. Use these scripts rather than manually invoking Python when possible.

### Windows

Use the bundled Windows launcher script:

```bat
[RUN]_WINDOWS.bat
```

What it does:

- changes to the launcher root directory
- uses the embedded Python runtime at `windows_python/python.exe`
- checks for an internet connection
- if connected, attempts to update the repository using Portable Git from `PortableGit/cmd/git.exe`
- upgrades required Python packages
- launches `src/main.py`

Important:

- You do **not** need a separate Python installation on Windows.
- You do **not** need a separate Git installation if the portable Git bundle is present.
- The launcher is intended to work out of the box using the packaged runtime.

### Linux

Use the Linux startup script:

```bash
./[RUN]_LINUX.sh
```

What it does:

- changes to the script directory
- checks for `python3`
- creates a local `.venv` environment if one does not already exist
- installs or upgrades dependencies from `requirements.txt`
- detects Raspberry Pi hardware and installs GPIO support packages when appropriate
- launches the application via `src/main.py`

Important:

- Linux requires a system `python3` installation to bootstrap the virtual environment.
- The script manages its own virtual environment, so developers do not need a global Python environment.

---

## 3. Project Structure

The repository is organized into the following primary directories and files:

```text
Atomic-launcher/
├── assets/              # launcher UI assets and button graphics
├── audio/               # shared sound and music files
├── data/                # persistent JSON data files and defaults
├── games/               # installed/managed game packages
├── src/                 # main application source code
│   ├── Drivers/         # optional input drivers (GPIO, controllers)
│   ├── Machines/        # background loaders and installer logic
│   ├── Managers/        # application service classes (audio, state)
│   ├── Manifests/       # static manifests like music track mapping
│   ├── States/          # UI states/screens (Library, Store, Options)
│   ├── Tools/           # helper utilities and JSON loaders
│   ├── UI/              # screen-specific UI components and widgets
│   ├── settings.py      # global constants, paths, default configs
│   └── main.py          # application entry point
├── windows_python/      # bundled Windows Python runtime
├── PortableGit/         # bundled Windows Git runtime
├── requirements.txt     # Python package dependencies
├── [RUN]_WINDOWS.bat    # Windows startup script
└── [RUN]_LINUX.sh       # Linux startup script
```

### Key directories

- `src/Drivers/`: optional hardware input support such as Raspberry Pi GPIO.
- `src/Machines/`: background asset import and repository-based game installation.
- `src/Managers/`: handles audio playback and application state routing.
- `src/States/`: contains the different launcher screens and state logic.
- `src/UI/`: reusable UI widgets and screen-specific presentation classes.
- `src/Tools/`: small utility helpers for JSON loading, timing, and asset scaling.

---

## 4. Core Architecture

The launcher is built around a state-driven interface:

- `src/main.py` initializes the runtime and enters the main event loop.
- `src/Managers/state_manager.py` switches between active screens and routes input.
- `src/States/` contains the screen implementations for Library, Store, Options, and Game Preview.
- `src/UI/` contains reusable widgets such as buttons, sliders, and sidebars.
- `src/Managers/audio_manager.py` centralizes music and sound playback.
- `src/Machines/game_installing_machine.py` handles cloning, updating, and removing game repositories.
- `src/Tools/data_loading_tools.py` manages JSON save/load with fallback defaults.

The launcher renders to a fixed internal resolution and scales to the operating display, so UI components should generally work with that virtual window size.

---

## 5. Running the Launcher

### Recommended flow

1. open a terminal in the launcher root
2. on Windows: run `[RUN]_WINDOWS.bat`
3. on Linux: run `./[RUN]_LINUX.sh`

### Direct launch

If you need to run the code directly for debugging, use:

```bash
python src/main.py
```

But for normal development and execution on this repository, prefer the platform scripts because they initialize the environment and keep the launcher configuration consistent.

---

## 6. Dependencies

Dependencies are listed in `requirements.txt` and include:

- `pygame-ce`
- `pytmx`
- `gpiozero`
- `RPi.GPIO`
- `pigpio`
- `lgpio`
- `opencv-python`

### Windows

The Windows runtime bundle installs Python and runs dependencies through the embedded `windows_python/python.exe`.

### Linux

The Linux script creates `.venv` and installs the requirements automatically. On Raspberry Pi hardware it also installs GPIO support packages.

---

## 7. Adding or Inspecting Games

Installed games are stored under `games/`.

The launcher tracks installed game state and version information through game directories and `version.json` files. If you are adding a new game or inspecting installer behavior, use the `games/` structure as a reference.

---

## 8. Contribution Workflow

### Recommended process

1. fork the repository
2. clone your fork locally
3. create a feature branch
4. make changes with clear comments and docstrings
5. test using `[RUN]_WINDOWS.bat` or `./[RUN]_LINUX.sh`
6. commit and push your work
7. open a pull request with a description of your changes

### Coding guidelines

- keep features modular and isolated
- prefer small, self-contained changes
- document new classes and major methods
- keep UI and state logic separate when possible
- use the existing `src/` folders as templates for new functionality

---

## 9. Notes for Raspberry Pi and GPIO

On Linux, `[RUN]_LINUX.sh` detects Raspberry Pi hardware and installs required GPIO backends:

- `python3-rpi.gpio`
- `python3-pigpio`
- `python3-lgpio`

The project also includes `src/Drivers/raspberry_pi_gpio.py` for mapping GPIO buttons into Pygame events.

---

## Final Notes

This documentation is meant to be up-to-date with the current repository and startup scripts. If you update `[RUN]_WINDOWS.bat` or `[RUN]_LINUX.sh`, please also update this file so future developers always have the correct startup instructions.
