package com.tariff.tariff_backend.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.tariff.tariff_backend.config.CorsConfig;
import com.tariff.tariff_backend.config.SecurityConfiguration;
import com.tariff.tariff_backend.dto.PasswordUpdateDTO;
import com.tariff.tariff_backend.dto.UserManagementDTO;
import com.tariff.tariff_backend.dto.UsernameUpdateDTO;
import com.tariff.tariff_backend.exception.UserManagementException;
import com.tariff.tariff_backend.model.user_management.UsernameUpdateResponse;
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
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
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

    // ... add these methods inside UserManagementControllerTest class ...

    // --- New tests for GET / ---
    
    @Test
    @WithMockUser(roles = "ADMIN")
    public void getAllUsers_AsAdmin_InternalError() throws Exception {
        when(jwtService.hasRole(any(), eq("admin"))).thenReturn(true);
        when(userManagementService.getAllUsers()).thenThrow(new RuntimeException("DB is down"));

        mockMvc.perform(get("/api/v1/users/")
                .header("Authorization", "Bearer fake-token-for-admin"))
                .andExpect(status().isInternalServerError()) // 500
                .andExpect(jsonPath("$.message").value("Internal Server Error"));
    }

    // --- New tests for GET /{requestedUsername} ---

    @Test
    @WithMockUser(username = "test-user")
    public void getUser_InternalError() throws Exception {
        when(jwtService.extractUsername(any())).thenReturn("test-user");
        when(userManagementService.getUserByUsername("test-user", "test-user"))
                .thenThrow(new RuntimeException("DB is down"));

        mockMvc.perform(get("/api/v1/users/{requestedUsername}", "test-user")
                        .header("Authorization", "Bearer fake-token"))
                .andExpect(status().isInternalServerError()) // 500
                .andExpect(jsonPath("$").value("Internal Server Error"));
    }

    // --- New tests for DELETE /{id} ---

    @Test
    @WithMockUser(roles = "USER") // Test non-admin
    public void deleteUser_AsUser_ShouldBeForbidden() throws Exception {
        when(jwtService.hasRole(any(), eq("admin"))).thenReturn(false);

        mockMvc.perform(delete("/api/v1/users/{id}", UUID.randomUUID())
                        .header("Authorization", "Bearer fake-token"))
                .andExpect(status().isForbidden()); // 403
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    public void deleteUser_AsAdmin_Success() throws Exception {
        UUID id = UUID.randomUUID();
        when(jwtService.hasRole(any(), eq("admin"))).thenReturn(true);
        doNothing().when(userManagementService).deleteUser(id);

        mockMvc.perform(delete("/api/v1/users/{id}", id)
                        .header("Authorization", "Bearer fake-token"))
                .andExpect(status().isOk()) // 200
                .andExpect(jsonPath("$.message").value("Deleted Successfully"));
    }
    
    @Test
    @WithMockUser(roles = "ADMIN")
    public void deleteUser_AsAdmin_UserNotFound() throws Exception {
        UUID id = UUID.randomUUID();
        when(jwtService.hasRole(any(), eq("admin"))).thenReturn(true);
        doThrow(new UserManagementException("User not found"))
            .when(userManagementService).deleteUser(id);

        mockMvc.perform(delete("/api/v1/users/{id}", id)
                        .header("Authorization", "Bearer fake-token"))
                .andExpect(status().isBadRequest()) // 400
                .andExpect(jsonPath("$.message").value("User not found"));
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    public void deleteUser_AsAdmin_InternalError() throws Exception {
        UUID id = UUID.randomUUID();
        when(jwtService.hasRole(any(), eq("admin"))).thenReturn(true);
        doThrow(new RuntimeException("DB is down"))
            .when(userManagementService).deleteUser(id);

        mockMvc.perform(delete("/api/v1/users/{id}", id)
                        .header("Authorization", "Bearer fake-token"))
                .andExpect(status().isInternalServerError()) // 500
                .andExpect(jsonPath("$").value("Internal Server Error"));
    }
    
    // --- New tests for PUT /{id} ---

    @Test
    @WithMockUser(roles = "USER") // Test non-admin
    public void updateUser_AsUser_ShouldBeForbidden() throws Exception {
        when(jwtService.hasRole(any(), eq("admin"))).thenReturn(false);

        mockMvc.perform(put("/api/v1/users/{id}", UUID.randomUUID())
                        .header("Authorization", "Bearer fake-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(new UserManagementDTO())))
                .andExpect(status().isForbidden()); // 403
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    public void updateUser_AsAdmin_Success() throws Exception {
        UUID id = UUID.randomUUID();
        UserManagementDTO dto = new UserManagementDTO(id, "user", "default");

        when(jwtService.hasRole(any(), eq("admin"))).thenReturn(true);
        doNothing().when(userManagementService).updateUser(eq(id), any(UserManagementDTO.class));

        mockMvc.perform(put("/api/v1/users/{id}", id)
                        .header("Authorization", "Bearer fake-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(dto)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("Updated Successfully"));
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    public void updateUser_AsAdmin_UserNotFound() throws Exception {
        UUID id = UUID.randomUUID();
        UserManagementDTO dto = new UserManagementDTO(id, "user", "default");

        when(jwtService.hasRole(any(), eq("admin"))).thenReturn(true);
        doThrow(new UserManagementException("User not found"))
            .when(userManagementService).updateUser(eq(id), any(UserManagementDTO.class));

        mockMvc.perform(put("/api/v1/users/{id}", id)
                        .header("Authorization", "Bearer fake-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(dto)))
                .andExpect(status().isBadRequest()) // 400
                .andExpect(jsonPath("$.message").value("User not found"));
    }
    
    @Test
    @WithMockUser(roles = "ADMIN")
    public void updateUser_AsAdmin_InternalError() throws Exception {
        UUID id = UUID.randomUUID();
        UserManagementDTO dto = new UserManagementDTO(id, "user", "default");

        when(jwtService.hasRole(any(), eq("admin"))).thenReturn(true);
        doThrow(new RuntimeException("DB is down"))
            .when(userManagementService).updateUser(eq(id), any(UserManagementDTO.class));

        mockMvc.perform(put("/api/v1/users/{id}", id)
                        .header("Authorization", "Bearer fake-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(dto)))
                .andExpect(status().isInternalServerError()) // 500
                .andExpect(jsonPath("$").value("Internal Server Error"));
    }

    @Test
    @WithMockUser(username = "test-user")
    public void updateUsername_InternalError() throws Exception {
        UUID id = UUID.randomUUID();
        UsernameUpdateDTO dto = new UsernameUpdateDTO("newName");

        when(jwtService.extractUsername(any())).thenReturn("test-user");
        doThrow(new RuntimeException("DB is down"))
            .when(userManagementService).updateUsername(any(), any(), any());

        mockMvc.perform(put("/api/v1/users/{id}/username", id)
                .header("Authorization", "Bearer fake-token")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(dto)))
                .andExpect(status().isInternalServerError()) // 500
                .andExpect(jsonPath("$.message").value("Internal Server Error"));
    }

    // --- New tests for PUT /{id}/password ---

    @Test
    @WithMockUser(username = "self-user")
    public void updatePassword_Success() throws Exception {
        UUID id = UUID.randomUUID();
        PasswordUpdateDTO dto = new PasswordUpdateDTO("newPassword123");

        when(jwtService.extractUsername(any())).thenReturn("self-user");
        doNothing().when(userManagementService).updatePassword(eq(id), eq("self-user"), eq("newPassword123"));
        
        mockMvc.perform(put("/api/v1/users/{id}/password", id)
                        .header("Authorization", "Bearer fake-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(dto)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("Password updated successfully"));
    }
    
    @Test
    @WithMockUser(username = "self-user")
    public void updatePassword_Fail_ServiceError() throws Exception {
        UUID id = UUID.randomUUID();
        PasswordUpdateDTO dto = new PasswordUpdateDTO("newPassword123");

        when(jwtService.extractUsername(any())).thenReturn("self-user");
        doThrow(new UserManagementException("User not authorized"))
            .when(userManagementService).updatePassword(any(), any(), any());
        
        mockMvc.perform(put("/api/v1/users/{id}/password", id)
                        .header("Authorization", "Bearer fake-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(dto)))
                .andExpect(status().isBadRequest()) // 400
                .andExpect(jsonPath("$.message").value("User not authorized"));
    }

    @Test
    @WithMockUser(username = "self-user")
    public void updatePassword_InternalError() throws Exception {
        UUID id = UUID.randomUUID();
        PasswordUpdateDTO dto = new PasswordUpdateDTO("newPassword1s");

        when(jwtService.extractUsername(any())).thenReturn("self-user");
        doThrow(new RuntimeException("DB is down"))
            .when(userManagementService).updatePassword(any(), any(), any());
        
        mockMvc.perform(put("/api/v1/users/{id}/password", id)
                        .header("Authorization", "Bearer fake-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(dto)))
                .andExpect(status().isInternalServerError()) // 500
                .andExpect(jsonPath("$.message").value("Internal Server Error"));
    }
}