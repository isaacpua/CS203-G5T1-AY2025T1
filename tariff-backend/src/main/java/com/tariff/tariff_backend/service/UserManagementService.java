package com.tariff.tariff_backend.service;

import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.dto.UserManagementDTO;
import com.tariff.tariff_backend.exception.UserManagementException;
import com.tariff.tariff_backend.model.Role;
import com.tariff.tariff_backend.model.User;
import com.tariff.tariff_backend.repository.UserRepo;
import com.tariff.tariff_backend.repository.RoleRepo;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class UserManagementService {
    private final UserRepo userRepo;
    private final RoleRepo roleRepo;

    public UserManagementDTO getUserByUsername(String jwtUsername, String requestedUsername)
            throws UserManagementException {
        if (!jwtUsername.equals(requestedUsername)) {
            throw new UserManagementException("You are not authorised to access this resource.");
        }
        Optional<User> optionalUser = userRepo.findByUsername(requestedUsername);
        if (optionalUser.isEmpty()) {
            throw new UserManagementException(
                    "User with username " + requestedUsername + " cannot be found in the database.");
        }
        User user = optionalUser.get();
        UserManagementDTO result = convertToDTO(user);
        return result;
    }

    public List<UserManagementDTO> getAllUsers() {
        List<User> users = userRepo.findAll();
        List<UserManagementDTO> userMgmtDTOs = users.stream()
                .map(this::convertToDTO)
                .collect(Collectors.toList());
        return userMgmtDTOs;
    }

    public void deleteUser(UUID id) throws UserManagementException {
        if (!userRepo.existsById(id)) {
            throw new UserManagementException("User with id " + id + " cannot be found in the database.");
        }
        userRepo.deleteById(id);
    }

    public void updateUser(UUID id, UserManagementDTO dto) throws UserManagementException {
        Optional<User> optionalUser = userRepo.findById(id);
        if (optionalUser.isEmpty()) {
            throw new UserManagementException("User with id " + id + " cannot be found in the database.");
        }

        User user = optionalUser.get();
        user.setUsername(dto.getUsername());

        Optional<Role> optionalRole = roleRepo.findByName(dto.getRole());
        if (optionalRole.isEmpty()) {
            throw new UserManagementException("Role " + dto.getRole() + " does not exist.");
        }
        Role role = optionalRole.get();
        user.setRole(role);

        userRepo.save(user);
    }

    public void updateUsername(UUID userId, String jwtUsername, String newUsername) throws UserManagementException {
        // Find user by ID
        Optional<User> optionalUser = userRepo.findById(userId);
        if (optionalUser.isEmpty()) {
            throw new UserManagementException("User with id " + userId + " cannot be found in the database.");
        }

        User user = optionalUser.get();

        if (!user.getUsername().equals(jwtUsername)) {
            throw new UserManagementException("You are not authorized to update this user's username.");
        }

        // Check if username already exists (case-insensitive)
        Optional<User> existingUser = userRepo.findByUsername(newUsername);
        if (existingUser.isPresent() && !existingUser.get().getId().equals(userId)) {
            throw new UserManagementException("Username '" + newUsername + "' is already taken.");
        }

        // Update username
        user.setUsername(newUsername);
        userRepo.save(user);
    }

    private UserManagementDTO convertToDTO(User user) {
        return UserManagementDTO.builder()
                .id(user.getId())
                .username(user.getUsername())
                .role(user.getRole().getName())
                .build();
    }
}
