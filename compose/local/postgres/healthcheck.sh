#!/bin/sh
# Simple PostgreSQL healthcheck script

pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" -h localhost