package com.tariff.tariff_backend.service;

import io.github.cdimascio.dotenv.Dotenv;

public class LoadEnvVar {
    public static void loadEnvVar() {
        // Load .env file
        Dotenv dotenv = Dotenv.load();
        
        // Set system properties
        dotenv.entries().forEach(entry -> 
            System.setProperty(entry.getKey(), entry.getValue())
        );
    }
}
