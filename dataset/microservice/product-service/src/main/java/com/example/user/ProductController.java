package com.example.product;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ProductController {
    @GetMapping("/products/hello")
    public String hello() {
        return "Hello from product-service!";
    }
} 