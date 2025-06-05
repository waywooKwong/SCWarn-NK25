FROM eclipse-temurin:17-jre
VOLUME /tmp
COPY target/product-service-*.jar app.jar
EXPOSE 8083
ENTRYPOINT ["java","-jar","/app.jar"] 