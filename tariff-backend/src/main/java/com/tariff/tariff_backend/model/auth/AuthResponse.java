package com.tariff.tariff_backend.model.auth;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.Builder;

@Data
@Builder
@Schema(description = "Authentication response containing operation result and access token")
public class AuthResponse {
    
    @Schema(
        description = "Indicates whether the authentication operation was successful",
        example = "true",
        required = true
    )
    private Boolean success;
    
    @Schema(
        description = "Response message providing details about the operation result",
        example = "Login successful",
        required = true
    )
    private String message;
    
    @Schema(
        description = "JWT access token for authenticated requests. Only present on successful authentication.",
        example = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        nullable = true
    )
    private String accessToken;
}
