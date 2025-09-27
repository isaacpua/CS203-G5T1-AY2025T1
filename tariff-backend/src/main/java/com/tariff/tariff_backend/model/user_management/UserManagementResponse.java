package com.tariff.tariff_backend.model.user_management;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import java.util.List;
import com.tariff.tariff_backend.dto.UserManagementDTO;
import lombok.Builder;

@Data
@Builder
@Schema(description = "Response for user management operations")
public class UserManagementResponse {
    
    @Schema(description = "Operation result message", example = "Users retrieved successfully")
    private String message;
    
    @Schema(description = "List of users (only present in getAllUsers response)")
    private List<UserManagementDTO> users;
}
