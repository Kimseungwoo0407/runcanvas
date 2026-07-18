FROM eclipse-temurin:25-jre-jammy

ARG GRAPHHOPPER_VERSION=11.0
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /graphhopper /data \
    && curl -fsSL \
       "https://repo1.maven.org/maven2/com/graphhopper/graphhopper-web/${GRAPHHOPPER_VERSION}/graphhopper-web-${GRAPHHOPPER_VERSION}.jar" \
       -o /graphhopper/graphhopper-web.jar

WORKDIR /graphhopper
COPY graphhopper.yml ./
COPY foot.json ./runcanvas-foot.json

EXPOSE 8989 8990
ENTRYPOINT ["java", "-Xms1g", "-Xmx4g", "-jar", "/graphhopper/graphhopper-web.jar", "server", "/graphhopper/graphhopper.yml"]
