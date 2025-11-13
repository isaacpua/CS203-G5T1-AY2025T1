package com.tariff.tariff_backend.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.tariff.tariff_backend.dto.UserDTO;
import com.tariff.tariff_backend.model.auth.AuthResponse;
import com.tariff.tariff_backend.service.AuthenticationService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/v1/auth")
@CrossOrigin(origins = "http://localhost:5173")
@Tag(name = "Authentication", description = "User authentication and authorization endpoints")
public class AuthenticationController {

    private final AuthenticationService authenticationService;
    public AuthenticationController(AuthenticationService authenticationService) {
        this.authenticationService = authenticationService;
    }

    @Operation(
        summary = "Register new user",
        description = "Creates a new user account with the provided credentials"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "User registered successfully",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = AuthResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid user data or user already exists",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = AuthResponse.class))),
        @ApiResponse(responseCode = "500", description = "Internal server error",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = AuthResponse.class)))
    })
    @PostMapping("/register")
    public ResponseEntity<?> register(
        @Valid
        @Parameter(description = "User registration details", required = true)
        @RequestBody UserDTO user) {
        AuthResponse authRes = authenticationService.register(user);
        if (!authRes.getSuccess()) {
            if (authRes.getMessage().startsWith("Internal Server Error")) {
                return ResponseEntity.internalServerError().body(authRes);
            }
            return ResponseEntity.badRequest().body(authRes);
        }
        return ResponseEntity.ok(authRes);
    }

    @Operation(
        summary = "User login",
        description = "Authenticates user credentials and returns access token"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Login successful",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = AuthResponse.class))),
        @ApiResponse(responseCode = "401", description = "Invalid credentials",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = AuthResponse.class))),
        @ApiResponse(responseCode = "500", description = "Internal server error",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = AuthResponse.class)))
    })
    @PostMapping("/login")
    public ResponseEntity<?> login(
        @Valid
        @Parameter(description = "User login credentials", required = true)
        @RequestBody UserDTO user) {
        AuthResponse authRes = authenticationService.login(user);
        if (!authRes.getSuccess()) {
            if (authRes.getMessage().startsWith("Internal Server Error")) {
                return ResponseEntity.internalServerError().body(authRes);
            }
            return ResponseEntity.status(401).body(authRes);
        }
        return ResponseEntity.ok(authRes);
    }

    @Operation(
        summary = "Verify JWT token",
        description = "Validates the provided JWT token and returns verification status"
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Token is valid",
            content = @Content(mediaType = "text/plain", schema = @Schema(type = "string", example = "Token is valid"))),
        @ApiResponse(responseCode = "400", description = "Token is invalid or malformed",
            content = @Content(mediaType = "text/plain", schema = @Schema(type = "string", example = "Token is invalid")))
    })
    @PostMapping("/verifyJWT")
    public ResponseEntity<?> verifyToken(
        @Parameter(description = "Bearer token in Authorization header", required = true, example = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        @RequestHeader("Authorization") String authHeader) {
        // Remove "Bearer "
        String token = authHeader.replace("Bearer ", "").trim();

        if (authenticationService.validateToken(token)) {
            return ResponseEntity.ok("Token is valid");
        }
        return ResponseEntity.badRequest().body("Token is invalid");
    }
}
