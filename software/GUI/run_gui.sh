#!/bin/bash

cd /home/stellarmate/Desktop || exit 1
nohup python3 GUI/stellarmate_gui.py >/dev/null 2>&1 &
nohup python3 GUI/generate_curve.py >/dev/null 2>&1 &
nohup python3 GUI/fits_to_jpeg.py >/dev/null 2>&1 &