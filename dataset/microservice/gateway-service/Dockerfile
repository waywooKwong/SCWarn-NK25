FROM eclipse-temurin:17-jre
VOLUME /tmp
COPY target/gateway-service-*.jar app.jar
EXPOSE 8081
ENTRYPOINT ["java","-jar","/app.jar"] 