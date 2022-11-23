#!/ausr/bin/env bash

fe_dependencies_has_changed () {
	git diff origin/develop -- docker/slam_base_fe.Dockerfile
	git diff origin/develop -- ui/common 
	git diff origin/develop -- ui/dms/package.json
	git diff origin/develop -- ui/admin/package.json
	git diff origin/develop -- ui/dashboard/package.json
	git diff origin/develop -- ui/pipeline/package.json
	git diff origin/develop -- ui/react-planner/package.json
	git diff origin/develop -- ui/potential-view/package.json
	git diff origin/develop -- ui/package.json
} 

get_development_version () {
	git show origin/develop:docker/.env | grep BASE_FE_IMAGE_VERSION | cut -d "=" -f 2
}


if [[ $(fe_dependencies_has_changed) ]] ; then
	echo "FE dependencies/common has changed, bumping up base image number"

	CURRENT_NUMBER=$(get_development_version)
	NEXT_NUMBER=$((CURRENT_NUMBER +1))
	echo "Current version: $CURRENT_NUMBER, bumping up to: $NEXT_NUMBER"
	sed "s/BASE_FE_IMAGE_VERSION=$CURRENT_NUMBER/BASE_FE_IMAGE_VERSION=$NEXT_NUMBER/" -i $(pwd)/docker/.env
	
	git config --global user.email circleci@circleci
	git config --global user.name CircleCI

	git add $(pwd)/docker/.env
	git commit -m "Bump up base fe image to $NEXT_NUMBER"
	git push -u origin HEAD
	
else 
	echo "no changed"
fi
