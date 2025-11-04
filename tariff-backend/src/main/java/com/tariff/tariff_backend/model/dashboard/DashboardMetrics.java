package com.tariff.tariff_backend.model.dashboard;

import java.util.List;

import com.tariff.tariff_backend.dto.TariffPatchDTO;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "Paginated response containing tariff data with pagination metadata")
public class DashboardMetrics {
    
    @Schema(description = "List of tariff items for the current page", required = true)
    private List<TariffPatchDTO> content;
    
    @Schema(description = "Current page number (0-based)", example = "0", required = true)
    private int number;
    
    @Schema(description = "Total number of available pages", example = "10", required = true)
    private int totalPages;
    
    @Schema(description = "Total number of tariff records across all pages", example = "245", required = true)
    private long totalElements;
}
