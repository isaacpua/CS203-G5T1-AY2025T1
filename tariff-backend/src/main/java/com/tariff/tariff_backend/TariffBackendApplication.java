package com.tariff.tariff_backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import com.tariff.tariff_backend.service.LoadEnvVar;

@SpringBootApplication
public class TariffBackendApplication {

	public static void main(String[] args) {
		LoadEnvVar.loadEnvVar();
		SpringApplication.run(TariffBackendApplication.class, args);
	}
}
