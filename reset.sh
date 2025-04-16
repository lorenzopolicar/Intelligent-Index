#!/bin/bash

source .venv/bin/activate

# Define the PostgreSQL connection URI
DB_URI="postgresql://postgres:postgres@localhost:5432/postgres?sslmode=disable"

echo "Dropping table 'store' if it exists..."
psql "$DB_URI" -c "DROP TABLE IF EXISTS store CASCADE;"
if [ $? -ne 0 ]; then
    echo "Error dropping table 'store'. Exiting."
    exit 1
fi

echo "Dropping table 'store_migrations' if it exists..."
psql "$DB_URI" -c "DROP TABLE IF EXISTS store_migrations CASCADE;"
if [ $? -ne 0 ]; then
    echo "Error dropping table 'store_migrations'. Exiting."
    exit 1
fi

echo "Dropping table 'store_vectors' if it exists..."
psql "$DB_URI" -c "DROP TABLE IF EXISTS store_vectors CASCADE;"
if [ $? -ne 0 ]; then
    echo "Error dropping table 'store_vectors'. Exiting."
    exit 1
fi

echo "Dropping table 'vector_migrations' if it exists..."
psql "$DB_URI" -c "DROP TABLE IF EXISTS vector_migrations CASCADE;"
if [ $? -ne 0 ]; then
    echo "Error dropping table 'vector_migrations'. Exiting."
    exit 1
fi

echo "Tables dropped successfully."
sudo service postgresql restart

echo "Removing LightRAG..."
rm -rf ./intellidesign
