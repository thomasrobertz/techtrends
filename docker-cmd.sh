#!/bin/sh
pwd
ls -la
echo "Init db and start app..."
python init_db.py
python app.py
echo "App started"