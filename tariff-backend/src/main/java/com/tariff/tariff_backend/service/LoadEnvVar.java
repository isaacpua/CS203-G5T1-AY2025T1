package com.tariff.tariff_backend.service;

import io.github.cdimascio.dotenv.Dotenv;

public class LoadEnvVar {
    public static void loadEnvVar() {
        try {
            // Only load .env in local development
            Dotenv dotenv = Dotenv.configure()
                .ignoreIfMissing()  // Don't crash if .env doesn't exist
                .load();
            
            dotenv.entries().forEach(e -> 
                System.setProperty(e.getKey(), e.getValue())
            );
        } catch (Exception e) {
            // In Docker, env vars are already set by docker-compose
            System.out.println("No .env file found, using system environment variables");
        }
    }
}
