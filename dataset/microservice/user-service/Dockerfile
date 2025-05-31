FROM eclipse-temurin:17-jre
VOLUME /tmp
COPY target/user-service-*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java","-jar","/app.jar"] 