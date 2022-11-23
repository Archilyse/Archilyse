#!/bin/bash

# Copyright © 2017 Google Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

IFS=$'\n\t'
set -eou pipefail

if [[ "${1}" == '-h' || "${1}" == '--help' ]]; then
	cat >&2 <<"EOF"
housekeeping_images.sh cleans up tagged or untagged images pushed for a given repository (an image name without a tag/digest)
and except the given number most recent images
USAGE:
  housekeeping_images.sh REPOSITORY
EXAMPLE
  housekeeping_images.sh eu.gcr.io/YOUR_PROJECT/IMAGE_NAME
  would clean up everything under the eu.gcr.io/test-project/php repository
  pushed except for the 5 most recent images
EOF
	exit 1
fi

main() {
	local C=0
	IMAGE="${1}"
	NUMBER_OF_IMAGES_TO_REMAIN=30

	DATE=$(gcloud container images list-tags $IMAGE --limit=unlimited \
		--sort-by=~TIMESTAMP --format=json | TZ=/usr/share/zoneinfo/UTC jq -r '.['$NUMBER_OF_IMAGES_TO_REMAIN'].timestamp.datetime | sub("(?<before>.*):"; .before ) | strptime("%Y-%m-%d %H:%M:%S%z") | mktime | strftime("%Y-%m-%d")')

	for digest in $(gcloud container images list-tags $IMAGE --limit=unlimited --sort-by=~TIMESTAMP \
		--filter="timestamp.datetime < '${DATE}'" --format='get(digest)'); do
		(
			set -x
			gcloud container images delete -q --force-delete-tags "${IMAGE}@${digest}"
		)
		let C=C+1
	done
	echo "Deleted ${C} images in ${IMAGE}." >&2
}

main "${1}"