package com.tariff.tariff_backend.model.user_management;

import com.tariff.tariff_backend.dto.UserManagementDTO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
@Schema(description = "Response containing user details")
public class UserResponse {
    
    @Schema(description = "Operation result message", example = "Retrieved user details successfully", required = true)
    String message;
    
    @Schema(description = "User details", required = true)
    UserManagementDTO user;
}
