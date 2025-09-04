package com.tariff.tariff_backend.model.auth;
import lombok.Data;
import lombok.Builder;

@Data
@Builder
public class AuthResponse {
    private Boolean success;
    private String message;
    private String accessToken;
}
