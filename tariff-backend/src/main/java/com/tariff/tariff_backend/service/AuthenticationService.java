package com.tariff.tariff_backend.service;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.model.User;
import com.tariff.tariff_backend.repository.UserRepo;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class AuthenticationService {
    private final UserRepo userRepo;
    private final JwtService jwtService;
    private final PasswordEncoder passwordEncoder;


    public User signup(User user) {
        user.setPassword(passwordEncoder.encode(user.getPassword()));
        System.out.println("Reached service, saving user...");
        System.out.println(user);
        return userRepo.save(user);
    }






    // *** TESTING PURPOSES ONLY, REMOVE LATER ***
    public String getJwt(String username) {
        User user = userRepo.findByUsername(username).orElseThrow();
        return jwtService.generateToken(java.util.Collections.emptyMap(), user);
    }
    public String getUserFromJwt(String token) {
        return jwtService.extractUsername(token);
    }
    public boolean isValid(java.util.Map<String, String> request) {
        String token = request.get("token");
        String username = request.get("username");
        User user = userRepo.findByUsername(username).orElseThrow();
        return jwtService.isTokenValid(token, user);
    }
    // *** TESTING PURPOSES ONLY, REMOVE LATER ***
}
