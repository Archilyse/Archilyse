ARG GCP_REGISTRY_PROJECT
ARG BASE_FE_IMAGE_VERSION

# Compiles pipeline code
FROM $GCP_REGISTRY_PROJECT/slam_base_fe:$BASE_FE_IMAGE_VERSION as pipeline
WORKDIR /dep/pipeline/
COPY ui/pipeline /dep/pipeline
RUN ng build --prod --deployUrl=ui-assets/ --sourceMap=false --buildOptimizer=true

# Compiles admin code
FROM $GCP_REGISTRY_PROJECT/slam_base_fe:$BASE_FE_IMAGE_VERSION as admin
WORKDIR /dep/admin/
COPY /docker/.env /dep/admin/.env
COPY /docker/.env.local /dep/admin/.env.local
COPY /ui/admin/ /dep/admin/
RUN npm run build

# Compiles dms code
FROM $GCP_REGISTRY_PROJECT/slam_base_fe:$BASE_FE_IMAGE_VERSION as dms
WORKDIR /dep/dms/
COPY /docker/.env /dep/dms/.env
COPY /docker/.env.local /dep/dms/.env.local
COPY /ui/dms/ /dep/dms/
RUN npm run build

# Compiles dashboard code
FROM $GCP_REGISTRY_PROJECT/slam_base_fe:$BASE_FE_IMAGE_VERSION as dashboard
WORKDIR /dep/dashboard
COPY /docker/.env /dep/dashboard/.env
COPY /docker/.env.local /dep/dashboard/.env.local
COPY /ui/dashboard /dep/dashboard
RUN npm run build

# Compiles Editor V2 code
FROM $GCP_REGISTRY_PROJECT/slam_base_fe:$BASE_FE_IMAGE_VERSION as editorV2
WORKDIR /dep/react-planner
COPY /docker/.env /dep/react-planner/.env
COPY /docker/.env.local /dep/react-planner/.env.local
COPY /ui/react-planner /dep/react-planner
RUN npm run build

# Compiles Potential View V2 code
FROM $GCP_REGISTRY_PROJECT/slam_base_fe:$BASE_FE_IMAGE_VERSION as potential_view_v2
WORKDIR /dep/potential-view
COPY /docker/.env /dep/potential-view/.env
COPY /docker/.env.local /dep/potential-view/.env.local
COPY /ui/potential-view /dep/potential-view
RUN npm run build

# Final image based on openresty
FROM openresty/openresty:1.19.9.1-12-alpine AS nginx

RUN apk update && apk --no-cache add tini

RUN rm -rf /etc/nginx/conf.d
COPY docker/nginx/run.sh /src/run.sh

ENV PATH=/src:$PATH
RUN chown -R nobody /etc/nginx /src
RUN mkdir -m 755 /var/log/nginx

COPY --from=dashboard /dep/dashboard/dist               /src/ui/dashboard/dist
COPY --from=pipeline  /dep/pipeline/dist                /src/ui/dist
COPY --from=dms       /dep/dms/dist                     /src/ui/dms/dist
COPY --from=admin     /dep/admin/dist                   /src/ui/admin/dist
COPY --from=editorV2  /dep/react-planner/dist      /src/ui/react-planner/dist
COPY --from=potential_view_v2  /dep/potential-view/dist      /src/ui/potential-view/dist

WORKDIR /src/

EXPOSE 80
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/src/run.sh"]

COPY docker/nginx/nginx.conf /etc/nginx/conf.d/app.conf
