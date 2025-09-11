package com.tariff.tariff_backend.controller;

import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.tariff.tariff_backend.model.user_management.UserManagementResponse;
import com.tariff.tariff_backend.service.UserManagementService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;

@RestController
@RequestMapping("/api/v1/users")
public class UserManagementController {
    private UserManagementService userMgmtSvc;
    public UserManagementController(UserManagementService userMgmtSvc) {
        this.userMgmtSvc = userMgmtSvc;
    }

    @GetMapping("/")
    public ResponseEntity<?> getAllUsers() {
        UserManagementResponse userMgmtRes = userMgmtSvc.getAllUsers();
        if (!userMgmtRes.getSuccess()) {
            if (userMgmtRes.getMessage().startsWith("Internal Server Error")) {
                return ResponseEntity.internalServerError().body(userMgmtRes);
            }
            return ResponseEntity.badRequest().body(userMgmtRes);
        }
        return ResponseEntity.ok(userMgmtRes);
    }
    
}
