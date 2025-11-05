package com.tariff.tariff_backend.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.tariff.tariff_backend.dto.UserDTO;
import com.tariff.tariff_backend.model.auth.AuthResponse;
import com.tariff.tariff_backend.service.AuthenticationService;
import com.tariff.tariff_backend.service.JwtService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
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
class AuthenticationControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private AuthenticationService authenticationService;

    @MockBean
    private JwtService jwtService;

    @Test
    void register_ShouldReturnOk_WhenRegistrationIsSuccessful() throws Exception {
        // --- Arrange ---
        UserDTO userDTO = new UserDTO("newUser", "password123");
        
        AuthResponse successResponse = AuthResponse.builder()
                .success(true)
                .message("User registered successfully")
                .build();
        
        when(authenticationService.register(any(UserDTO.class))).thenReturn(successResponse);

        // --- Act & Assert ---
        mockMvc.perform(post("/api/v1/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(userDTO)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.message").value("User registered successfully"));
    }

    @Test
    void register_ShouldReturnBadRequest_WhenUserExists() throws Exception {
        // --- Arrange ---
        UserDTO userDTO = new UserDTO("existingUser", "password123");
        
        AuthResponse failResponse = AuthResponse.builder()
                .success(false)
                .message("User already exists")
                .build();

        when(authenticationService.register(any(UserDTO.class))).thenReturn(failResponse);

        // --- Act & Assert ---
        mockMvc.perform(post("/api/v1/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(userDTO)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.message").value("User already exists"));
    }
}