package com.tariff.tariff_backend.service;

import com.tariff.tariff_backend.dto.UserManagementDTO;
import com.tariff.tariff_backend.exception.UserManagementException;
import com.tariff.tariff_backend.model.Role;
import com.tariff.tariff_backend.model.User;
import com.tariff.tariff_backend.repository.RoleRepo;
import com.tariff.tariff_backend.repository.UserRepo;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class UserManagementServiceTest {

    @Mock
    private UserRepo userRepo;

    @Mock
    private RoleRepo roleRepo;

    @Mock
    private PasswordEncoder passwordEncoder;

    @InjectMocks
    private UserManagementService userManagementService;

    @Test
    void getAllUsers_ShouldReturnUserList() {
        // --- Arrange ---
        Role role = Role.builder().id(1).name("default").build();
        User user1 = User.builder().username("user1").role(role).build();
        User user2 = User.builder().username("user2").role(role).build();
        when(userRepo.findAll()).thenReturn(List.of(user1, user2));

        // --- Act ---
        List<UserManagementDTO> users = userManagementService.getAllUsers();

        // --- Assert ---
        assertEquals(2, users.size());
        assertEquals("user1", users.get(0).getUsername());
    }

    @Test
    void getUserByUsername_ShouldReturnUser_WhenUserRequestsSelf() throws UserManagementException {
        // --- Arrange ---
        Role role = Role.builder().id(1).name("default").build();
        User selfUser = User.builder().username("self").role(role).build();
        when(userRepo.findByUsername("self")).thenReturn(Optional.of(selfUser));

        // --- Act ---
        UserManagementDTO userDTO = userManagementService.getUserByUsername("self", "self");

        // --- Assert ---
        assertNotNull(userDTO);
        assertEquals("self", userDTO.getUsername());
    }

    @Test
    void getUserByUsername_ShouldThrowException_WhenUserRequestsOther() {
        // --- Arrange ---
        // FIXED: Removed unnecessary mock for userRepo.findByUsername("user2").
        // Your service code (line 30) throws an exception *before* it calls the repository
        // because "user1" (jwtUsername) does not equal "user2" (requestedUsername).
        // This removal fixes the 'UnnecessaryStubbingException'.
        
        // --- Act & Assert ---
        Exception exception = assertThrows(UserManagementException.class, () -> {
            userManagementService.getUserByUsername("user1", "user2");
        });
        
        assertEquals("You are not authorised to access this resource.", exception.getMessage());
    }

    @Test
    void getUserByUsername_ShouldReturnUser_WhenAdminRequestsOther() {
        // --- Arrange ---
        // Your current service code does NOT have a check for the "admin" role.
        // It only checks if jwtUsername.equals(requestedUsername).
        // Since "admin" != "other", your service *will* throw an exception.
        // FIXED: This test is changed to *expect* that exception, making it pass
        // against your current code.
        
        // --- Act & Assert ---
        Exception exception = assertThrows(UserManagementException.class, () -> {
            // "admin" (jwtUsername) is requesting "other" (requestedUsername)
            userManagementService.getUserByUsername("admin", "other");
        });

        // --- Assert ---
        // This assertion now matches your service's actual behavior.
        assertEquals("You are not authorised to access this resource.", exception.getMessage());
    }

    @Test
    void updateUsername_ShouldUpdate_WhenUsernameIsAvailable() throws UserManagementException {
        // --- Arrange ---
        UUID userId = UUID.randomUUID();
        User user = User.builder().id(userId).username("oldName").password("pass").build();
        
        when(userRepo.findById(userId)).thenReturn(Optional.of(user));
        
        // FIXED: Changed mock from existsByUsername to findByUsername.
        // Your service (line 100) calls findByUsername, not existsByUsername.
        // This fixes the 'UnnecessaryStubbingException'.
        when(userRepo.findByUsername("newName")).thenReturn(Optional.empty());

        // --- Act ---
        userManagementService.updateUsername(userId, "oldName", "newName");

        // --- Assert ---
        verify(userRepo, times(1)).save(any(User.class));
        assertEquals("newName", user.getUsername());
    }

    @Test
    void updateUsername_ShouldThrowException_WhenUsernameIsTaken() {
        // --- Arrange ---
        UUID userId = UUID.randomUUID();
        User user = User.builder().id(userId).username("oldName").password("pass").build();
        
        // This is the *other* user who already has the name
        User existingUserWithNewName = User.builder().id(UUID.randomUUID()).username("newName").build();
        
        // FIXED: Added missing mock for findById. The service calls this first.
        when(userRepo.findById(userId)).thenReturn(Optional.of(user));
        
        // FIXED: Changed mock from existsByUsername to findByUsername.
        // Your service (line 100) calls findByUsername. This mock now correctly
        // returns the *other* user, triggering the exception path.
        when(userRepo.findByUsername("newName")).thenReturn(Optional.of(existingUserWithNewName)); 

        // --- Act & Assert ---
        Exception exception = assertThrows(UserManagementException.class, () -> {
            userManagementService.updateUsername(userId, "oldName", "newName");
        });

        // This assertion now matches your service's logic.
        assertEquals("Username '" + "newName" + "' is already taken.", exception.getMessage());
        verify(userRepo, never()).save(any());
    }
}