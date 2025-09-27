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
@Schema(description = "Response for password update operations")
public class PasswordUpdateResponse {
    
    @Schema(description = "Operation result message", example = "Password updated successfully", required = true)
    private String message;
}
