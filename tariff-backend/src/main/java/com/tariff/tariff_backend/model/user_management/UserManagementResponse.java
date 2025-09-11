package com.tariff.tariff_backend.model.user_management;

import lombok.Data;

import java.util.List;

import com.tariff.tariff_backend.dto.UserManagementDTO;

import lombok.Builder;

@Data
@Builder
public class UserManagementResponse {
    private Boolean success;
    private String message;
    private List<UserManagementDTO> users;
}
