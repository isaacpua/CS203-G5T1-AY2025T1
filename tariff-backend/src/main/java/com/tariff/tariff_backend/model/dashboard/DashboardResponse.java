package com.tariff.tariff_backend.model.dashboard;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.AllArgsConstructor;

@Data
@AllArgsConstructor
@Schema(description = "Standard response for dashboard operations")
public class DashboardResponse {
    
    @Schema(description = "Indicates whether the operation was successful", example = "true", required = true)
    private Boolean success;
    
    @Schema(description = "Response message with operation details", example = "Tariff created successfully", required = true)
    private String message;
}
