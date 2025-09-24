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
		SpringApplication.run(TariffBackendApplication.class, args);
	}
}
