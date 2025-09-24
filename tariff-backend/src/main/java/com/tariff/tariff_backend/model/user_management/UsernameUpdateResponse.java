package com.tariff.tariff_backend.model.user_management;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UsernameUpdateResponse {
    private String message;
    private String newUsername;
}
