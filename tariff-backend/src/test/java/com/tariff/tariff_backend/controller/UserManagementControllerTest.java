package com.tariff.tariff_backend.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.tariff.tariff_backend.config.CorsConfig;
import com.tariff.tariff_backend.config.SecurityConfiguration;
import com.tariff.tariff_backend.dto.UserManagementDTO;
import com.tariff.tariff_backend.dto.UsernameUpdateDTO;
import com.tariff.tariff_backend.exception.UserManagementException;
import com.tariff.tariff_backend.security.JwtAuthenticationEntryPoint;
import com.tariff.tariff_backend.security.JwtAuthenticationFilter;
import com.tariff.tariff_backend.service.JwtService;
import com.tariff.tariff_backend.service.UserManagementService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
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
@Import({
    SecurityConfiguration.class, 
    CorsConfig.class,
    JwtAuthenticationEntryPoint.class,  // <-- ADD THIS
    JwtAuthenticationFilter.class       // <-- ADD THIS
})
class UserManagementControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private UserManagementService userManagementService;

    @MockBean
    private JwtService jwtService;


    @Test
    // **FIXED**: Use @WithMockUser to simulate a logged-in user
    @WithMockUser(roles = "USER") 
    void getAllUsers_ShouldFail_WhenNotAdmin() throws Exception {
        // --- Arrange ---
        // Mock the service call that checks the role
        when(jwtService.hasRole(any(), eq("admin"))).thenReturn(false);

        // --- Act & Assert ---
        mockMvc.perform(get("/api/v1/users/")
                // **FIXED**: We must provide a header, even if it's fake,
                // otherwise the controller returns 400 (Bad Request)
                .header("Authorization", "Bearer fake-token-for-user"))
                .andExpect(status().isForbidden()); // Now we expect 403 Forbidden
    }

    @Test
    // **FIXED**: Use @WithMockUser to simulate an admin
    @WithMockUser(roles = "admin") 
    void getAllUsers_ShouldSucceed_WhenAdmin() throws Exception {
        // --- Arrange ---
        UserManagementDTO userDTO = new UserManagementDTO(UUID.randomUUID(), "testuser", "default");
        
        when(jwtService.hasRole(any(), eq("admin"))).thenReturn(true);
        when(userManagementService.getAllUsers()).thenReturn(List.of(userDTO));

        // --- Act & Assert ---
        mockMvc.perform(get("/api/v1/users/")
                // **FIXED**: Provide the required header
                .header("Authorization", "Bearer fake-token-for-admin"))
                .andExpect(status().isOk())
                // **FIXED**: The response is an object {"users": [...]}, not just the list
                .andExpect(jsonPath("$.users[0].username").value("testuser"));
    }

    @Test
    @WithMockUser(username = "test-user")
    void updateUsername_ShouldFail_WhenServiceThrowsException() throws Exception {
        // --- Arrange ---
        UUID userId = UUID.randomUUID();
        UsernameUpdateDTO updateDTO = new UsernameUpdateDTO("newName");

        doThrow(new UserManagementException("Username already taken."))
            .when(userManagementService).updateUsername(any(), any(), any());
        
        when(jwtService.extractUsername(any())).thenReturn("test-user");

        // --- Act & Assert ---
        mockMvc.perform(put("/api/v1/users/{id}/username", userId)
                .header("Authorization", "Bearer fake-token") // Header is required
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(updateDTO)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message").value("Username already taken."));
    }
}