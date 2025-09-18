package com.tariff.tariff_backend.service;

import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

import org.springframework.dao.DataAccessException;
import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.dto.UserManagementDTO;
import com.tariff.tariff_backend.exception.UserManagementException;
import com.tariff.tariff_backend.model.Role;
import com.tariff.tariff_backend.model.User;
import com.tariff.tariff_backend.model.user_management.UserManagementResponse;
import com.tariff.tariff_backend.repository.UserRepo;
import com.tariff.tariff_backend.repository.RoleRepo;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class UserManagementService {
    private final UserRepo userRepo;
    private final RoleRepo roleRepo;

    public UserManagementResponse getAllUsers() {
        UserManagementResponse response = UserManagementResponse.builder()
            .message("Successfully got all users.")
            .success(true)
            .users(null)
            .build();
        try {
            List<User> users = userRepo.findAll();

            List<UserManagementDTO> userMgmtDTOs = users.stream()
                .map(this::convertToDTO)
                .collect(Collectors.toList());

            response.setUsers(userMgmtDTOs);
        } catch (DataAccessException e) {
            response.setSuccess(false);
            response.setMessage("Failed to retrieve users due to database errors.");
        } catch (Exception e) {
            response.setSuccess(false);
            response.setMessage("Internal Server Error: " + e.getMessage());
        }
        return response;
    }

    public UserManagementResponse deleteUser(UUID id) {
        UserManagementResponse response = UserManagementResponse.builder()
            .message("Successfully deleted the requested user.")
            .success(true)
            .build();
        try {
            if (!userRepo.existsById(id)) {
                throw new UserManagementException("User with id " + id + " cannot be found in the database.");
            }
            userRepo.deleteById(id);
        } catch (DataAccessException e) {
            response.setSuccess(false);
            response.setMessage("Failed to delete user due to database errors.");
        } catch (UserManagementException e) {
            response.setSuccess(false);
            response.setMessage(e.getMessage());
        } catch (Exception e) {
            response.setSuccess(false);
            response.setMessage("Internal Server Error: " + e.getMessage());
        }
        return response;
    }

    public UserManagementResponse updateUser(UUID id, UserManagementDTO dto) {
        UserManagementResponse response = UserManagementResponse.builder()
            .message("Successfully updated the requested user.")
            .success(true)
            .build();
        try {
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
        } catch (DataAccessException e) {
            response.setSuccess(false);
            response.setMessage("Failed to update user due to database errors.");
        } catch (UserManagementException e) {
            response.setSuccess(false);
            response.setMessage(e.getMessage());
        } catch (Exception e) {
            response.setSuccess(false);
            response.setMessage("Internal Server Error: " + e.getMessage());
        }
        return response;
    }

    private UserManagementDTO convertToDTO(User user) {
        return UserManagementDTO.builder()
            .id(user.getId())
            .username(user.getUsername())
            .role(user.getRole().getName())
            .build();
    }
}
