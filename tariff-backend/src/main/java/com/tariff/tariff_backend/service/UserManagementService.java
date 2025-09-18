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
  

    private UserManagementDTO convertToDTO(User user) {
        return UserManagementDTO.builder()
            .id(user.getId())
            .username(user.getUsername())
            .role(user.getRole().getName())
            .build();
    }
}
