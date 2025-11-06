package com.tariff.tariff_backend.service;

import io.github.cdimascio.dotenv.Dotenv;
import io.github.cdimascio.dotenv.DotenvEntry;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.MockedStatic;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.HashSet;
import java.util.Set;

// --- THIS IS THE FIX ---
import static org.junit.jupiter.api.Assertions.assertNotNull; 
// --- END OF FIX ---

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.mockStatic;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class LoadEnvVarTest {

    @Test
    void loadEnvVar_ShouldSetSystemProperties() {
        // Arrange
        Dotenv mockDotenv = mock(Dotenv.class);
        Set<DotenvEntry> entries = new HashSet<>();
        entries.add(new DotenvEntry("TEST_KEY", "TEST_VALUE"));

        when(mockDotenv.entries()).thenReturn(entries);

        // We must mock the static Dotenv.load() method
        try (MockedStatic<Dotenv> dotenvMockedStatic = mockStatic(Dotenv.class)) {
            dotenvMockedStatic.when(Dotenv::load).thenReturn(mockDotenv);

            // Act
            LoadEnvVar.loadEnvVar();

            // Assert
            assertEquals("TEST_VALUE", System.getProperty("TEST_KEY"));
        }
    }
    
    @Test
    void testConstructor() {
        // Cover the implicit public constructor
        assertNotNull(new LoadEnvVar());
    }
}