#!/bin/bash

DATE=`date '+%d_%m_%y_%R'`

pg_dump -U $POSTGRES_USER $POSTGRES_DB > autoria_$DATE.sql

