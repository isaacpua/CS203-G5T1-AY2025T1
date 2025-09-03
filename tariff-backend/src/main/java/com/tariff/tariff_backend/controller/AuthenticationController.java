package com.tariff.tariff_backend.controller;

import java.util.Map;

import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.tariff.tariff_backend.model.User;
import com.tariff.tariff_backend.service.AuthenticationService;



@RestController
@RequestMapping("/api/v1/auth")
@CrossOrigin(origins = "http://localhost:5173")

public class AuthenticationController {

    private final AuthenticationService authenticationService;
    public AuthenticationController(AuthenticationService authenticationService) {
        this.authenticationService = authenticationService;
    }


    @PostMapping("/signup")
    public User signup(@RequestBody User user) {
        System.out.println(user);
        System.out.println("Reached controller, calling service...");
        return authenticationService.signup(user);
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
