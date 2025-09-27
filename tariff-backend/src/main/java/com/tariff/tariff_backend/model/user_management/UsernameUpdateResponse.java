package com.tariff.tariff_backend.model.user_management;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "Response for username update operations")
public class UsernameUpdateResponse {
    
    @Schema(description = "Operation result message", example = "Username updated successfully", required = true)
    private String message;
    
    @Schema(description = "The new username that was set", example = "john_doe_updated", required = true)
    private String newUsername;
}
