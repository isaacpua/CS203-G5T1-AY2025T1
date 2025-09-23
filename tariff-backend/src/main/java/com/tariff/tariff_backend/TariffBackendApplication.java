package com.tariff.tariff_backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.web.config.EnableSpringDataWebSupport;

import com.tariff.tariff_backend.service.LoadEnvVar;

@SpringBootApplication
@EnableSpringDataWebSupport(pageSerializationMode = EnableSpringDataWebSupport.PageSerializationMode.VIA_DTO)
public class TariffBackendApplication {

	public static void main(String[] args) {
		LoadEnvVar.loadEnvVar();
		// Log whether JWT_SECRET was loaded from .env/system properties (masked)
		String jwt = System.getProperty("JWT_SECRET");
		if (jwt == null || jwt.isBlank()) {
			System.out.println("JWT_SECRET not found in system properties after LoadEnvVar().");
		} else {
			String masked = jwt.length() <= 10 ? "<short>" : jwt.substring(0,6) + "..." + jwt.substring(jwt.length()-4);
			System.out.println("JWT_SECRET loaded (masked)=" + masked);
		}
		SpringApplication.run(TariffBackendApplication.class, args);
	}
}
