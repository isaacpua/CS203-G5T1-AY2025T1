package com.tariff.tariff_backend.controller;

import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
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
            return ResponseEntity.badRequest().body(authRes);
        }
        return ResponseEntity.ok(authRes);
    }




    // *** TESTING PURPOSES ONLY, REMOVE LATER ***
    @GetMapping("/jwt")
    public String jwt(@RequestParam String username) {
        return authenticationService.getJwt(username);
    }
    @PostMapping("/jwtName")
    public String jwtName(@RequestBody String token) {
        return authenticationService.getUserFromJwt(token);
    }
    @PostMapping("/valid")
    public boolean isValid(@RequestBody Map<String, String> request) { 
        return authenticationService.isValid(request);
    }
    // *** TESTING PURPOSES ONLY, REMOVE LATER ***
}
