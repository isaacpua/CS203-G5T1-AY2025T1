package com.tariff.tariff_backend.service;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import static org.mockito.ArgumentMatchers.any;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import com.tariff.tariff_backend.dto.UserDTO;
import com.tariff.tariff_backend.model.Role;
import com.tariff.tariff_backend.model.User;
import com.tariff.tariff_backend.model.auth.AuthResponse;
import com.tariff.tariff_backend.repository.RoleRepo;
import com.tariff.tariff_backend.repository.UserRepo;

@ExtendWith(MockitoExtension.class)
class AuthenticationServiceTest {

    @Mock
    private UserRepo userRepo;

    @Mock
    private RoleRepo roleRepo;

    @Mock
    private JwtService jwtService;

    @Mock
    private PasswordEncoder passwordEncoder;

    @InjectMocks
    private AuthenticationService authenticationService;

    @Test
    void register_ShouldSucceed_WhenUsernameIsNew() {
        // --- Arrange ---
        UserDTO userDTO = new UserDTO("newUser", "password123");
        Role defaultRole = Role.builder().id(1).name("default").build();
        User savedUser = User.builder().username("newUser").password("encodedPassword").role(defaultRole).build();

        when(userRepo.existsByUsername("newUser")).thenReturn(false);
        when(roleRepo.findById(1)).thenReturn(Optional.of(defaultRole));
        when(passwordEncoder.encode("password123")).thenReturn("encodedPassword");
        when(userRepo.save(any(User.class))).thenReturn(savedUser);

        // --- Act ---
        AuthResponse response = authenticationService.register(userDTO);

        // --- Assert ---
        assertTrue(response.getSuccess());
        assertEquals("Registration successful", response.getMessage());
        assertNull(response.getAccessToken());
        verify(userRepo, times(1)).save(any(User.class));
    }

    @Test
    void register_ShouldFail_WhenUsernameExists() {
        // --- Arrange ---
        UserDTO userDTO = new UserDTO("existingUser", "password123");
        when(userRepo.existsByUsername("existingUser")).thenReturn(true);

        // --- Act ---
        AuthResponse response = authenticationService.register(userDTO);

        // --- Assert ---
        assertFalse(response.getSuccess());
        assertEquals("User with username existingUser already exists", response.getMessage());
        verify(userRepo, never()).save(any(User.class));
    }

    @Test
    void login_ShouldSucceed_WhenCredentialsAreValid() {
        // --- Arrange ---
        UserDTO userDTO = new UserDTO("testUser", "password123");
        Role defaultRole = Role.builder().id(1).name("default").build();
        User existingUser = User.builder()
                .username("testUser")
                .password("encodedPassword")
                .role(defaultRole)
                .build();
        
        Map<String, Object> claims = new HashMap<>();
        claims.put("roles", "default");

        when(userRepo.findByUsername("testUser")).thenReturn(Optional.of(existingUser));
        when(passwordEncoder.matches("password123", "encodedPassword")).thenReturn(true);
        when(jwtService.generateToken(claims, existingUser)).thenReturn("test.token.jwt");

        // --- Act ---
        AuthResponse response = authenticationService.login(userDTO);

        // --- Assert ---
        assertTrue(response.getSuccess());
        // THIS IS THE CORRECTED LINE:
        assertEquals("Login successful", response.getMessage()); 
        assertEquals("test.token.jwt", response.getAccessToken());
    }

    @Test
    void login_ShouldFail_WhenPasswordIsIncorrect() {
        // --- Arrange ---
        UserDTO userDTO = new UserDTO("testUser", "wrongPassword");
        User existingUser = User.builder()
                .username("testUser")
                .password("encodedPassword")
                .build();
        
        when(userRepo.findByUsername("testUser")).thenReturn(Optional.of(existingUser));
        when(passwordEncoder.matches("wrongPassword", "encodedPassword")).thenReturn(false);

        // --- Act ---
        AuthResponse response = authenticationService.login(userDTO);

        // --- Assert ---
        assertFalse(response.getSuccess());
        assertEquals("The username or password you entered is incorrect.", response.getMessage());
        assertNull(response.getAccessToken());
        verify(jwtService, never()).generateToken(any(), any());
    }
}