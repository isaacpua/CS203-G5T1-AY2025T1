package com.tariff.tariff_backend.controller;

import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.tariff.tariff_backend.dto.PasswordUpdateDTO;
import com.tariff.tariff_backend.dto.UserManagementDTO;
import com.tariff.tariff_backend.dto.UsernameUpdateDTO;
import com.tariff.tariff_backend.exception.AuthException;
import com.tariff.tariff_backend.exception.UserManagementException;
import com.tariff.tariff_backend.model.user_management.PasswordUpdateResponse;
import com.tariff.tariff_backend.model.user_management.UserManagementResponse;
import com.tariff.tariff_backend.model.user_management.UserResponse;
import com.tariff.tariff_backend.model.user_management.UsernameUpdateResponse;
import com.tariff.tariff_backend.service.JwtService;
import com.tariff.tariff_backend.service.UserManagementService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;

import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;

@RestController
@RequestMapping("/api/v1/users")
@Tag(name = "User Management", description = "User administration and profile management operations")
public class UserManagementController {
    private UserManagementService userMgmtSvc;
    private JwtService jwtService;

    public UserManagementController(UserManagementService userMgmtSvc, JwtService jwtService) {
        this.userMgmtSvc = userMgmtSvc;
        this.jwtService = jwtService;
    }

    @Operation(
        summary = "Get all users",
        description = "Retrieves a list of all users in the system. Requires admin role.",
        security = @SecurityRequirement(name = "Bearer Authentication")
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Users retrieved successfully",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = UserManagementResponse.class))),
        @ApiResponse(responseCode = "403", description = "Insufficient permissions - admin role required",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = UserManagementResponse.class))),
        @ApiResponse(responseCode = "500", description = "Internal server error",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = UserManagementResponse.class)))
    })
    @GetMapping("/")
    public ResponseEntity<?> getAllUsers(
        @Parameter(description = "Bearer token for admin authentication", required = true)
        @RequestHeader("Authorization") String authHeader) {
        UserManagementResponse response = UserManagementResponse.builder().build();
        try {
            if (authHeader == null || !jwtService.hasRole(jwtService.getTokenFromHeader(authHeader), "admin")) {
                throw new AuthException("You do not have enough permissions.");
            }
            response.setUsers(userMgmtSvc.getAllUsers());
            return ResponseEntity.ok().body(response);
        } catch (AuthException e) {
            response.setMessage(e.getMessage());
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(response);
        } catch (Exception e) {
            System.out.println(e.getMessage());
            response.setMessage("Internal Server Error");
            return ResponseEntity.internalServerError().body(response);
        }
    }

    @Operation(
        summary = "Get user by username",
        description = "Retrieves user details by username. Users can only access their own profile unless they are admins.",
        security = @SecurityRequirement(name = "Bearer Authentication")
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "User details retrieved successfully",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = UserResponse.class))),
        @ApiResponse(responseCode = "400", description = "User not found or access denied",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = UserResponse.class))),
        @ApiResponse(responseCode = "500", description = "Internal server error",
            content = @Content(mediaType = "text/plain", schema = @Schema(type = "string", example = "Internal Server Error")))
    })
    @GetMapping("/{requestedUsername}")
    public ResponseEntity<?> getUser(
        @Parameter(description = "Bearer token for authentication", required = true)
        @RequestHeader("Authorization") String authHeader,
        @Parameter(description = "Username of the user to retrieve", required = true, example = "john_doe")
        @PathVariable String requestedUsername) {
        UserResponse response = UserResponse.builder().build();
        try {
            String jwtUsername = jwtService.extractUsername(jwtService.getTokenFromHeader(authHeader));
            UserManagementDTO userDetails = userMgmtSvc.getUserByUsername(jwtUsername, requestedUsername);
            response.setUser(userDetails);
            response.setMessage("Retrieved user details successfully");
            return ResponseEntity.ok().body(response);
        } catch (UserManagementException e) {
            response.setMessage(e.getMessage());
            return ResponseEntity.badRequest().body(response);
        } catch (Exception e) {
            System.out.println(e.getMessage());
            return ResponseEntity.internalServerError().body("Internal Server Error");
        }
    }

    @Operation(
        summary = "Delete user",
        description = "Deletes a user account by ID. Requires admin role.",
        security = @SecurityRequirement(name = "Bearer Authentication")
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "User deleted successfully",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = UserManagementResponse.class))),
        @ApiResponse(responseCode = "400", description = "User not found or cannot be deleted",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = UserManagementResponse.class))),
        @ApiResponse(responseCode = "403", description = "Insufficient permissions - admin role required",
            content = @Content(mediaType = "text/plain", schema = @Schema(type = "string", example = "You do not have enough permissions."))),
        @ApiResponse(responseCode = "500", description = "Internal server error",
            content = @Content(mediaType = "text/plain", schema = @Schema(type = "string", example = "Internal Server Error")))
    })
    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteUser(
        @Parameter(description = "Bearer token for admin authentication", required = true)
        @RequestHeader("Authorization") String authHeader,
        @Parameter(description = "UUID of the user to delete", required = true, 
                  example = "550e8400-e29b-41d4-a716-446655440000")
        @PathVariable UUID id) {
        UserManagementResponse response = UserManagementResponse.builder().build();
        try {
            if (authHeader == null || !jwtService.hasRole(jwtService.getTokenFromHeader(authHeader), "admin")) {
                throw new AuthException("You do not have enough permissions.");
            }
            userMgmtSvc.deleteUser(id);
            response.setMessage("Deleted Successfully");
            return ResponseEntity.ok().body(response);
        } catch (AuthException e) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(e.getMessage());
        } catch (UserManagementException e) {
            response.setMessage(e.getMessage());
            return ResponseEntity.badRequest().body(response);
        } catch (Exception e) {
            System.out.println(e.getMessage());
            return ResponseEntity.internalServerError().body("Internal Server Error");
        }
    }

    @Operation(
        summary = "Update user",
        description = "Updates user information by ID. Requires admin role.",
        security = @SecurityRequirement(name = "Bearer Authentication")
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "User updated successfully",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = UserManagementResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid user data or user not found",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = UserManagementResponse.class))),
        @ApiResponse(responseCode = "403", description = "Insufficient permissions - admin role required",
            content = @Content(mediaType = "text/plain", schema = @Schema(type = "string", example = "You do not have enough permissions."))),
        @ApiResponse(responseCode = "500", description = "Internal server error",
            content = @Content(mediaType = "text/plain", schema = @Schema(type = "string", example = "Internal Server Error")))
    })
    @PutMapping("/{id}")
    public ResponseEntity<?> updateUser(
        @Parameter(description = "Bearer token for admin authentication", required = true)
        @RequestHeader("Authorization") String authHeader,
        @Parameter(description = "UUID of the user to update", required = true,
                  example = "550e8400-e29b-41d4-a716-446655440000")
        @PathVariable UUID id,
        @Valid
        @Parameter(description = "Updated user information", required = true)
        @RequestBody UserManagementDTO dto) {
        UserManagementResponse response = UserManagementResponse.builder().build();
        try {
            if (authHeader == null || !jwtService.hasRole(jwtService.getTokenFromHeader(authHeader), "admin")) {
                throw new AuthException("You do not have enough permissions.");
            }
            userMgmtSvc.updateUser(id, dto);
            response.setMessage("Updated Successfully");
            return ResponseEntity.ok().body(response);
        } catch (AuthException e) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(e.getMessage());
        } catch (UserManagementException e) {
            response.setMessage(e.getMessage());
            return ResponseEntity.badRequest().body(response);
        } catch (Exception e) {
            System.out.println(e.getMessage());
            return ResponseEntity.internalServerError().body("Internal Server Error");
        }
    }

    @Operation(
        summary = "Update username",
        description = "Updates the username for a user. Users can only update their own username.",
        security = @SecurityRequirement(name = "Bearer Authentication")
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Username updated successfully",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = UsernameUpdateResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid username or user not found",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = UsernameUpdateResponse.class))),
        @ApiResponse(responseCode = "500", description = "Internal server error",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = UsernameUpdateResponse.class)))
    })
    @PutMapping("/{id}/username")
    public ResponseEntity<?> updateUsername(
        @Parameter(description = "Bearer token for user authentication", required = true)
        @RequestHeader("Authorization") String authHeader,
        @Parameter(description = "UUID of the user whose username to update", required = true,
                  example = "550e8400-e29b-41d4-a716-446655440000")
        @PathVariable UUID id,
        @Parameter(description = "New username data", required = true)
        @RequestBody @Valid UsernameUpdateDTO dto) {
        UsernameUpdateResponse response = UsernameUpdateResponse.builder().build();
        try {
            String jwtUsername = jwtService.extractUsername(jwtService.getTokenFromHeader(authHeader));
            userMgmtSvc.updateUsername(id, jwtUsername, dto.getUsername());
            response.setMessage("Username updated successfully");
            response.setNewUsername(dto.getUsername());
            return ResponseEntity.ok().body(response);
        } catch (UserManagementException e) {
            response.setMessage(e.getMessage());
            return ResponseEntity.badRequest().body(response);
        } catch (Exception e) {
            System.out.println("Error updating username: " + e.getMessage());
            response.setMessage("Internal Server Error");
            return ResponseEntity.internalServerError().body(response);
        }
    }

    @Operation(
        summary = "Update password",
        description = "Updates the password for a user. Users can only update their own password.",
        security = @SecurityRequirement(name = "Bearer Authentication")
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Password updated successfully",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = PasswordUpdateResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid password or user not found",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = PasswordUpdateResponse.class))),
        @ApiResponse(responseCode = "500", description = "Internal server error",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = PasswordUpdateResponse.class)))
    })
    @PutMapping("/{id}/password")
    public ResponseEntity<?> updatePassword(
        @Parameter(description = "Bearer token for user authentication", required = true)
        @RequestHeader("Authorization") String authHeader,
        @Parameter(description = "UUID of the user whose password to update", required = true,
                  example = "550e8400-e29b-41d4-a716-446655440000")
        @PathVariable UUID id,
        @Parameter(description = "New password data", required = true)
        @RequestBody @Valid PasswordUpdateDTO dto) {
        PasswordUpdateResponse response = PasswordUpdateResponse.builder().build();
        try {
            String jwtUsername = jwtService.extractUsername(jwtService.getTokenFromHeader(authHeader));
            userMgmtSvc.updatePassword(id, jwtUsername, dto.getPassword());
            response.setMessage("Password updated successfully");
            return ResponseEntity.ok().body(response);
        } catch (UserManagementException e) {
            response.setMessage(e.getMessage());
            return ResponseEntity.badRequest().body(response);
        } catch (Exception e) {
            System.out.println("Error updating password: " + e.getMessage());
            response.setMessage("Internal Server Error");
            return ResponseEntity.internalServerError().body(response);
        }
    }
}
