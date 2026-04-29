# cackle

Dual webcam capture service for the AI lifting coach.

## Features

- Front + side webcam capture
- Timestamped frames
- ZeroMQ frame metadata publishing
- Designed for local inference pipeline

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run

```bash
cackle
```