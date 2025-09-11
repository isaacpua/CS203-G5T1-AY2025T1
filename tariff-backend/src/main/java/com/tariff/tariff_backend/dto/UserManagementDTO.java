package com.tariff.tariff_backend.dto;
import lombok.Data;

import java.util.UUID;

import lombok.Builder;

@Data
@Builder
public class UserManagementDTO {
    private UUID id;
    private String username;
    private String roles;
}
