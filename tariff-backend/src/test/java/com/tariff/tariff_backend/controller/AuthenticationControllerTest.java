package com.tariff.tariff_backend.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.tariff.tariff_backend.config.ApplicationConfig;
import com.tariff.tariff_backend.config.CorsConfig;
import com.tariff.tariff_backend.config.SecurityConfiguration;
import com.tariff.tariff_backend.dto.UserDTO;
import com.tariff.tariff_backend.exception.AuthException;
import com.tariff.tariff_backend.model.auth.AuthResponse;
import com.tariff.tariff_backend.security.JwtAuthenticationEntryPoint;
import com.tariff.tariff_backend.security.JwtAuthenticationFilter;
import com.tariff.tariff_backend.service.AuthenticationService;
import com.tariff.tariff_backend.service.JwtService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(AuthenticationController.class)
@Import({
    SecurityConfiguration.class, 
    CorsConfig.class,
    JwtAuthenticationEntryPoint.class,  // <-- ADD THIS
    JwtAuthenticationFilter.class       // <-- ADD THIS
})public class AuthenticationControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private AuthenticationService authenticationService;

    // Mocks required by SecurityConfiguration
    @MockBean
    private JwtService jwtService;

    @MockBean
    private ApplicationConfig applicationConfig;

    @Test
    public void testRegister() throws Exception {
        // FIX: UserDTO constructor is (email, password)
        UserDTO userDTO = new UserDTO("test@example.com", "password");
        // FIX: AuthResponse builder has .success() and .message()
        AuthResponse authResponse = AuthResponse.builder().success(true).message("Registered").build();

        when(authenticationService.register(any(UserDTO.class))).thenReturn(authResponse);

        mockMvc.perform(post("/api/v1/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(userDTO)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true));
    }

    @Test
    public void testRegister_UserAlreadyExists() throws Exception {
        UserDTO userDTO = new UserDTO("test@example.com", "password");
        AuthResponse authResponse = AuthResponse.builder().success(false).message("User with this email already exists").build();

        when(authenticationService.register(any(UserDTO.class))).thenReturn(authResponse);

        mockMvc.perform(post("/api/v1/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(userDTO)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message").value("User with this email already exists"));
    }

    @Test
    public void testLogin() throws Exception {
        // FIX: UserDTO constructor is (email, password)
        UserDTO userDTO = new UserDTO("test@example.com", "password");
        AuthResponse authResponse = AuthResponse.builder().success(true).message("Authenticated").build();

        // FIX: Service method is login(UserDTO)
        when(authenticationService.login(any(UserDTO.class))).thenReturn(authResponse);

        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(userDTO)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true));
    }

    @Test
    public void testLogin_BadCredentials() throws Exception {
        UserDTO userDTO = new UserDTO("test@example.com", "wrongpassword");
        AuthResponse authResponse = AuthResponse.builder().success(false).message("Invalid email or password").build();

        // FIX: Service method is login(UserDTO)
        when(authenticationService.login(any(UserDTO.class))).thenReturn(authResponse);

        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(userDTO)))
                .andExpect(status().isUnauthorized()) // Controller returns 401 for login failure
                .andExpect(jsonPath("$.message").value("Invalid email or password"));
    }
}