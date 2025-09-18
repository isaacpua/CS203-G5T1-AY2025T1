package com.tariff.tariff_backend.controller;

import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.tariff.tariff_backend.dto.UserManagementDTO;
import com.tariff.tariff_backend.exception.AuthException;
import com.tariff.tariff_backend.exception.UserManagementException;
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


    @DeleteMapping("/{id}")
    @SecurityRequirement(name = "Authorization")
    public ResponseEntity<?> deleteUser(@RequestHeader("Authorization") String authHeader, @PathVariable UUID id) {
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
    

    @PutMapping("/{id}")
    @SecurityRequirement(name = "Authorization")
    public ResponseEntity<?> updateUser(@RequestHeader("Authorization") String authHeader, @PathVariable UUID id, @RequestBody UserManagementDTO dto) {
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
}
