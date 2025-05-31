package com.example.gateway;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class GatewayController {
    @GetMapping("/gateway/hello")
    public String hello() {
        return "Hello from gateway-service!";
    }
} 