package com.tariff.tariff_backend.controller;

import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.tariff.tariff_backend.dto.UserManagementDTO;
import com.tariff.tariff_backend.model.user_management.UserManagementResponse;
import com.tariff.tariff_backend.service.JwtService;
import com.tariff.tariff_backend.service.UserManagementService;

import io.swagger.v3.oas.annotations.security.SecurityRequirement;

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
public class UserManagementController {
    private UserManagementService userMgmtSvc;
    private JwtService jwtService;
    public UserManagementController(UserManagementService userMgmtSvc, JwtService jwtService) {
        this.userMgmtSvc = userMgmtSvc;
        this.jwtService = jwtService;
    }

    @GetMapping("/")
    @SecurityRequirement(name = "Authorization")
    public ResponseEntity<?> getAllUsers(@RequestHeader("Authorization") String authHeader) {
        // There has got be a better way of writing once and applying everywhere needed
        UserManagementResponse failedRes = UserManagementResponse.builder()
            .success(false)
            .build();
        if (authHeader == null) {
            failedRes.setMessage("Authorization token is missing.");
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(failedRes);
        }
        String token = jwtService.getTokenFromHeader(authHeader);
        if (!jwtService.isAdmin(token)) {
            failedRes.setMessage("You do not have enough permissions.");
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(failedRes);
        }
        
        UserManagementResponse userMgmtRes = userMgmtSvc.getAllUsers();
        if (!userMgmtRes.getSuccess()) {
            if (userMgmtRes.getMessage().startsWith("Internal Server Error")) {
                return ResponseEntity.internalServerError().body(userMgmtRes);
            }
            return ResponseEntity.badRequest().body(userMgmtRes);
        }
        return ResponseEntity.ok(userMgmtRes);
    }

    @DeleteMapping("/{id}")
    @SecurityRequirement(name = "Authorization")
    public ResponseEntity<?> deleteUser(@RequestHeader("Authorization") String authHeader, @PathVariable UUID id) {
        // There has got be a better way of writing once and applying everywhere needed
        UserManagementResponse failedRes = UserManagementResponse.builder()
            .success(false)
            .build();
        if (authHeader == null) {
            failedRes.setMessage("Authorization token is missing.");
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(failedRes);
        }
        String token = jwtService.getTokenFromHeader(authHeader);
        if (!jwtService.isAdmin(token)) {
            failedRes.setMessage("You do not have enough permissions.");
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(failedRes);
        }

        UserManagementResponse userMgmtRes = userMgmtSvc.deleteUser(id);
        if (!userMgmtRes.getSuccess()) {
            if (userMgmtRes.getMessage().startsWith("Internal Server Error")) {
                return ResponseEntity.internalServerError().body(userMgmtRes);
            }
            return ResponseEntity.badRequest().body(userMgmtRes);
        }
        return ResponseEntity.ok(userMgmtRes);
    }

    @PutMapping("/{id}")
    @SecurityRequirement(name = "Authorization")
    public ResponseEntity<?> updateUser(@RequestHeader("Authorization") String authHeader, @PathVariable UUID id, @RequestBody UserManagementDTO dto) {
        // There has got be a better way of writing once and applying everywhere needed
        UserManagementResponse failedRes = UserManagementResponse.builder()
            .success(false)
            .build();
        if (authHeader == null) {
            failedRes.setMessage("Authorization token is missing.");
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(failedRes);
        }
        String token = jwtService.getTokenFromHeader(authHeader);
        if (!jwtService.isAdmin(token)) {
            failedRes.setMessage("You do not have enough permissions.");
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(failedRes);
        }

        UserManagementResponse userMgmtRes = userMgmtSvc.updateUser(id, dto);
        if (!userMgmtRes.getSuccess()) {
            if (userMgmtRes.getMessage().startsWith("Internal Server Error")) {
                return ResponseEntity.internalServerError().body(userMgmtRes);
            }
            return ResponseEntity.badRequest().body(userMgmtRes);
        }
        return ResponseEntity.ok(userMgmtRes);
    }
}
