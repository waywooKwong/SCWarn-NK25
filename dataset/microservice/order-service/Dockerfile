FROM eclipse-temurin:17-jre
VOLUME /tmp
COPY target/order-service-*.jar app.jar
EXPOSE 8082
ENTRYPOINT ["java","-jar","/app.jar"] 