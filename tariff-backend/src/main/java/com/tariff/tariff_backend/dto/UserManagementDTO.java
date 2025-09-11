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
    private String roles;

    // Constructor without ID for create operations
    public UserManagementDTO(String username, String roles) {
        this.username = username;
        this.roles = roles;
        this.id = null;
    }
}
