#!/usr/bin/env bash
#

version_date=`date +%y%m%d`

# Copy results
gsutil -m rsync -rn results gs://genetics-portal-staging/finemapping/$version_date

# Tar the logs and copy over
tar -zcvf logs.tar.gz logs
gsutil -m cp logs.tar.gz gs://genetics-portal-staging/finemapping/$version_date/logs.tar.gz
