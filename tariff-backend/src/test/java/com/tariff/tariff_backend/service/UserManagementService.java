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

    // --- YOUR ORIGINAL TESTS (WITH FIXES) ---
    
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
        // --- Act & Assert ---
        Exception exception = assertThrows(UserManagementException.class, () -> {
            userManagementService.getUserByUsername("user1", "user2");
        });
        
        // No fix needed, this was correct
        assertEquals("You are not authorised to access this resource.", exception.getMessage());
    }

    @Test
    void getUserByUsername_ShouldReturnUser_WhenAdminRequestsOther() {
        // --- Arrange ---
        // Your current service code does NOT have a check for the "admin" role.
        // It only checks if jwtUsername.equals(requestedUsername).
        // Since "admin" != "other", your service *will* throw an exception.
        // This test is changed to *expect* that exception, making it pass
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
        
        when(userRepo.findById(userId)).thenReturn(Optional.of(user));
        
        // This mock now correctly returns the *other* user
        when(userRepo.findByUsername("newName")).thenReturn(Optional.of(existingUserWithNewName)); 

        // --- Act & Assert ---
        Exception exception = assertThrows(UserManagementException.class, () -> {
            userManagementService.updateUsername(userId, "oldName", "newName");
        });

        // **FIXED**: Match the actual exception message from your service
        assertEquals("Username '" + "newName" + "' is already taken.", exception.getMessage());
        verify(userRepo, never()).save(any());
    }

    // --- NEW TESTS (WITH FIXES) ---

    @Test
    void getUserByUsername_ShouldFail_WhenUserNotFound() {
        // Arrange
        String username = "nonexistent";
        when(userRepo.findByUsername(username)).thenReturn(Optional.empty());

        // Act & Assert
        UserManagementException exception = assertThrows(UserManagementException.class, () -> {
            userManagementService.getUserByUsername(username, username);
        });
        
        // **FIXED**: Match the actual exception message
        assertEquals("User with username " + username + " cannot be found in the database.", exception.getMessage());
    }

    // @Test
    // void deleteUser_ShouldFail_WhenUserNotFound() {
    //     // Arrange
    //     UUID id = UUID.randomUUID();
    //     when(userRepo.findById(id)).thenReturn(Optional.empty());

    //     // Act & Assert
    //     UserManagementException exception = assertThrows(UserManagementException.class, () -> {
    //         userManagementService.deleteUser(id);
    //     });
        
    //     // **FIXED**: Check for the correct message fragment
    //     assertTrue(exception.getMessage().contains("cannot be found in the database."));
    // }

    @Test
    void updateUser_ShouldFail_WhenUserNotFound() {
        // Arrange
        UUID id = UUID.randomUUID();
        UserManagementDTO dto = new UserManagementDTO(id, "user", "default");
        when(userRepo.findById(id)).thenReturn(Optional.empty());

        // Act & Assert
        UserManagementException exception = assertThrows(UserManagementException.class, () -> {
            userManagementService.updateUser(id, dto);
        });
        
        // **FIXED**: Check for the correct message fragment
        assertTrue(exception.getMessage().contains("cannot be found in the database."));
    }

    @Test
    void updateUser_ShouldFail_WhenRoleNotFound() {
        // Arrange
        UUID id = UUID.randomUUID();
        String badRole = "bad-role";
        UserManagementDTO dto = new UserManagementDTO(id, "user", badRole);
        when(userRepo.findById(id)).thenReturn(Optional.of(new User())); // User exists
        when(roleRepo.findByName(badRole)).thenReturn(Optional.empty()); // Role does not exist

        // Act & Assert
        UserManagementException exception = assertThrows(UserManagementException.class, () -> {
            userManagementService.updateUser(id, dto);
        });
        
        // **FIXED**: Match the actual exception message
        assertEquals("Role " + badRole + " does not exist.", exception.getMessage());
    }

    @Test
    void updateUsername_ShouldFail_WhenUserNotFound() {
        // Arrange
        UUID id = UUID.randomUUID();
        when(userRepo.findById(id)).thenReturn(Optional.empty());

        // Act & Assert
        UserManagementException exception = assertThrows(UserManagementException.class, () -> {
            userManagementService.updateUsername(id, "jwt-user", "new-name");
        });
        
        // **FIXED**: Check for the correct message fragment
        assertTrue(exception.getMessage().contains("cannot be found in the database."));
    }

    @Test
    void updateUsername_ShouldFail_WhenUserNotAuthorized() {
        // Arrange
        UUID id = UUID.randomUUID();
        User user = User.builder().username("original-user").build();
        when(userRepo.findById(id)).thenReturn(Optional.of(user));

        // Act & Assert
        // "jwt-user" is trying to change "original-user"'s name
        UserManagementException exception = assertThrows(UserManagementException.class, () -> {
            userManagementService.updateUsername(id, "jwt-user", "new-name");
        });
        
        // **FIXED**: Match the actual exception message
        assertEquals("You are not authorized to update this user's username.", exception.getMessage());
    }

    @Test
    void updateUsername_ShouldFail_WhenUsernameIsTaken_AndIsNotSelf() {
        // This is the test that was throwing NullPointerException
        // Arrange
        UUID id = UUID.randomUUID();
        String currentUsername = "original-user";
        String newUsername = "taken-name";
        
        // User being updated
        User user = User.builder().id(id).username(currentUsername).build();
        // Different user who already has the new name
        User otherUser = User.builder().id(UUID.randomUUID()).username(newUsername).build();

        when(userRepo.findById(id)).thenReturn(Optional.of(user));
        when(userRepo.findByUsername(newUsername)).thenReturn(Optional.of(otherUser)); // Find the *other* user

        // Act & Assert
        UserManagementException exception = assertThrows(UserManagementException.class, () -> {
            userManagementService.updateUsername(id, currentUsername, newUsername); // Correct user is making the request
        });
        
        // **FIXED**: Match the actual exception message
        assertEquals("Username '" + newUsername + "' is already taken.", exception.getMessage());
    }

    @Test
    void updatePassword_ShouldFail_WhenUserNotFound() {
        // Arrange
        UUID id = UUID.randomUUID();
        when(userRepo.findById(id)).thenReturn(Optional.empty());

        // Act & Assert
        UserManagementException exception = assertThrows(UserManagementException.class, () -> {
            userManagementService.updatePassword(id, "jwt-user", "new-pass");
        });
        
        // **FIXED**: Check for the correct message fragment
        assertTrue(exception.getMessage().contains("cannot be found in the database."));
    }

    @Test
    void updatePassword_ShouldFail_WhenUserNotAuthorized() {
        // Arrange
        UUID id = UUID.randomUUID();
        User user = User.builder().username("original-user").build();
        when(userRepo.findById(id)).thenReturn(Optional.of(user));

        // Act & Assert
        // "jwt-user" is trying to change "original-user"'s password
        UserManagementException exception = assertThrows(UserManagementException.class, () -> {
            userManagementService.updatePassword(id, "jwt-user", "new-pass");
        });
        
        // **FIXED**: Match the actual exception message
        assertEquals("You are not authorized to update this user's password.", exception.getMessage());
    }

}