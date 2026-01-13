FROM quay.io/cdis/amazonlinux-base:3.13-pythonnginx AS builder

USER root


RUN yum install -y \
    java-17-amazon-corretto-devel \
    tar \
    gzip \
    wget \
    && yum clean all \
    && rm -rf /var/cache/yum/*

ARG MAVEN_VERSION=3.9.9
RUN wget --tries=5 --retry-connrefused \
    "https://archive.apache.org/dist/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz" \
    -O /tmp/maven.tar.gz \
    && mkdir -p /opt/maven \
    && tar -xzf /tmp/maven.tar.gz -C /opt/maven --strip-components=1 \
    && rm -f /tmp/maven.tar.gz

ENV MAVEN_HOME=/opt/maven
ENV PATH="${MAVEN_HOME}/bin:${PATH}"

ENV JAVA_HOME=/usr/lib/jvm/java-17-amazon-corretto
ENV PATH="${JAVA_HOME}/bin:${PATH}"


RUN java -version && mvn --version

WORKDIR /build

COPY pom.xml .
RUN mvn dependency:go-offline -B -ntp


COPY src ./src
RUN mvn clean package spring-boot:repackage \
    -DskipTests \
    -Pboot \
    -DfinalName=hapi-fhir-jpaserver \
    -ntp


FROM gcr.io/distroless/java17-debian12:nonroot

WORKDIR /app


COPY --from=builder /build/target/ROOT.jar ./app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
