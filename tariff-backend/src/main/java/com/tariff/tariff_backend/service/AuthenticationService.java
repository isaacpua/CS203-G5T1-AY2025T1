package com.tariff.tariff_backend.service;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.dto.UserDTO;
import com.tariff.tariff_backend.exception.AuthException;
import com.tariff.tariff_backend.model.Role;
import com.tariff.tariff_backend.model.User;
import com.tariff.tariff_backend.model.auth.AuthResponse;
import com.tariff.tariff_backend.repository.RoleRepo;
import com.tariff.tariff_backend.repository.UserRepo;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class AuthenticationService {
    private final UserRepo userRepo;
    private final RoleRepo roleRepo;
    private final JwtService jwtService;
    private final PasswordEncoder passwordEncoder;


    public AuthResponse register(UserDTO user) {
        AuthResponse response = AuthResponse.builder()
            .success(true)
            .message("Registration successful")
            .build();
        String username = user.getUsername();
        String pw = passwordEncoder.encode(user.getPassword());
        try {
            if (userRepo.existsByUsername(username)) {
                throw new AuthException("User with username " + username + " already exists");
            }

            Role role = roleRepo.findById(1).orElseGet(()-> { // find default role, else create it
                Role newRole = Role.builder()
                    .id(1)
                    .name("default")
                    .build();
                return roleRepo.save(newRole);
            });

            System.out.println("ROLE ID ISSS: " + role.getId());
            // Create the User object to be saved
            User newUser = User.builder()
                .username(username)
                .password(pw)
                .role(role)
                .build();

            userRepo.save(newUser);
        } catch (AuthException e) {
            response.setSuccess(false);
            response.setMessage(e.getMessage());
        } catch (Exception e) {
            response.setSuccess(false);
            response.setMessage("Internal Server Error: " + e.getMessage());
        }
        return response;
    }

    public AuthResponse login(UserDTO user) {
        AuthResponse response = AuthResponse.builder()
            .success(true)
            .message("Login successful")
            .accessToken(null)
            .build();
        String username = user.getUsername();
        String pw = user.getPassword();
        try {
            // Check credentials against DB
            Optional<User> optionalUser = userRepo.findByUsername(username);
            if (optionalUser.isEmpty()) {
                throw new AuthException("The username or password you entered is incorrect.");
            }
            User matchingUser = optionalUser.get();

            if (!passwordEncoder.matches(pw, matchingUser.getPassword())) {
                // Why not just say password is incorrect?
                // An attacker will know that now the username is correct and they just need to spam passwords
                throw new AuthException("The username or password you entered is incorrect.");
            }

            // Generate an Access Token
            Map<String, Object> claims = new HashMap<>();
            claims.put("roles", matchingUser.getRole().getName());
            String accessToken = jwtService.generateToken(claims, matchingUser);
            response.setAccessToken(accessToken);
        } catch (AuthException e) {
            response.setSuccess(false);
            response.setMessage(e.getMessage());
        } catch (Exception e) {
            response.setSuccess(false);
            response.setMessage("Internal Server Error: " + e.getMessage());
        }
        return response;
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
    public boolean validateToken(String token) {
        return jwtService.isTokenValid(token);
    }
    // *** TESTING PURPOSES ONLY, REMOVE LATER ***
}
