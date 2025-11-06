package com.tariff.tariff_backend;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

@SpringBootTest
@TestPropertySource(properties = {
    // **FIXED**: Added MODE=PostgreSQL and NON_KEYWORDS=USER,YEAR
    "spring.datasource.url=jdbc:h2:mem:testdb;INIT=CREATE SCHEMA IF NOT EXISTS TARIFFS;MODE=PostgreSQL;NON_KEYWORDS=USER,YEAR",
    "spring.datasource.driver-class-name=org.h2.Driver",
    "spring.datasource.username=sa",
    "spring.datasource.password=password",
    "spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.H2Dialect",
    "spring.jpa.hibernate.ddl-auto=create-drop",
    "jwt.secret=a-very-long-and-random-secret-key-for-testing-purposes-only-123456789"
})
class DatabaseConnectionTest {

    @Test
    void testDatabaseConnection() {
    }
}