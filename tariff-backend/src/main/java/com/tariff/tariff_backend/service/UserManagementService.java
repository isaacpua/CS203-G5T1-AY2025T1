package com.tariff.tariff_backend.service;

import java.util.List;
import java.util.stream.Collectors;

import org.springframework.dao.DataAccessException;
import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.dto.UserManagementDTO;
import com.tariff.tariff_backend.model.User;
import com.tariff.tariff_backend.model.user_management.UserManagementResponse;
import com.tariff.tariff_backend.repository.UserRepo;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class UserManagementService {
    private final UserRepo userRepo;

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
            response.setMessage("Failed to retrieve users due to database errors.");
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
            .roles(user.getRoles())
            .build();
    }
}
