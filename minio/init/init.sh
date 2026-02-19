#!/bin/sh

echo "Starting MinIO initialization..."

echo $MINIO_USER

# Configure alias
until mc alias set local http://minio:9000 "$MINIO_USER" "$MINIO_PASSWORD"; do
  echo "Waiting for MinIO to become available..."
  sleep 2
done
echo "Successfully connected to MinIO"

# Bucket creation
create_bucket() {
  BUCKET=$1
  mc mb --ignore-existing local/$BUCKET
  echo "Bucket $BUCKET ready"
}

create_bucket $BUCKET_RAW
create_bucket $BUCKET_PROCESSED
create_bucket $BUCKET_OUTPUT
