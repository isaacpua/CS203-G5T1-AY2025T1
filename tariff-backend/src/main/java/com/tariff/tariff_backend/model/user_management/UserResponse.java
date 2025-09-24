package com.tariff.tariff_backend.model.user_management;

import com.tariff.tariff_backend.dto.UserManagementDTO;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class UserResponse {
    String message;
    UserManagementDTO user;
}
