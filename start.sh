#!/bin/bash
export MFS_MASTER='192.168.61.90'
export MARIO_IP='192.168.61.71'
python manage.py runserver -h 0.0.0.0
