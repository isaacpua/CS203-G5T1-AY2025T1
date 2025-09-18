package com.tariff.tariff_backend.dto;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.UUID;

import lombok.AllArgsConstructor;
import lombok.Builder;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserManagementDTO {
    private UUID id;
    private String username;
    private String role;

    // Constructor without ID for create operations
    public UserManagementDTO(String username, String role) {
        this.username = username;
        this.role = role;
        this.id = null;
    }
}
