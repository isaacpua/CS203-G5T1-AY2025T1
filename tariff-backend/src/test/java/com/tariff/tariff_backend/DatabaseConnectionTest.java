package com.tariff.tariff_backend;

import java.sql.Connection;

import javax.sql.DataSource;

import static org.assertj.core.api.Assertions.assertThat;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

import io.github.cdimascio.dotenv.Dotenv;

@SpringBootTest
class DatabaseConnectionTest {

    // This method runs BEFORE the application context is created for the test.
    // It loads the .env file and manually sets the properties for Spring.
    @DynamicPropertySource
    static void dynamicProperties(DynamicPropertyRegistry registry) {
        Dotenv dotenv = Dotenv.load();

        registry.add("spring.datasource.url", () -> dotenv.get("DB_URL"));
        registry.add("spring.datasource.username", () -> dotenv.get("DB_USERNAME"));
        registry.add("spring.datasource.password", () -> dotenv.get("DB_PASSWORD"));
    }

    @Autowired
    private DataSource dataSource;

    @Test
    void testDatabaseConnection() throws Exception {
        try (Connection connection = dataSource.getConnection()) {
            assertThat(connection).isNotNull();
            assertThat(connection.isValid(1)).isTrue();
            System.out.println("\nDatabase Connection successful!\n");
        }
    }
}
