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



@RestController
@RequestMapping("/api/v1/auth")
@CrossOrigin(origins = "http://localhost:5173")

public class AuthenticationController {

    private final AuthenticationService authenticationService;
    public AuthenticationController(AuthenticationService authenticationService) {
        this.authenticationService = authenticationService;
    }


    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody UserDTO user) {
        AuthResponse authRes = authenticationService.register(user);
        if (!authRes.getSuccess()) {
            if (authRes.getMessage().startsWith("Internal Server Error")) {
                return ResponseEntity.internalServerError().body(authRes);
            }
            return ResponseEntity.badRequest().body(authRes);
        }
        return ResponseEntity.ok(authRes);
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody UserDTO user) {
        AuthResponse authRes = authenticationService.login(user);
        if (!authRes.getSuccess()) {
            if (authRes.getMessage().startsWith("Internal Server Error")) {
                return ResponseEntity.internalServerError().body(authRes);
            }
            return ResponseEntity.status(401).body(authRes);
        }
        return ResponseEntity.ok(authRes);
    }




    @PostMapping("/verifyJWT")
    public ResponseEntity<?> postMethodName(@RequestHeader("Authorization") String authHeader) {
        // Remove "Bearer "
        String token = authHeader.replace("Bearer ", "").trim();

        if (authenticationService.validateToken(token)) {
            return ResponseEntity.ok("Token is valid");
        }
        return ResponseEntity.badRequest().body("Token is invalid");
    }
}
