package com.tariff.tariff_backend.dto.CalculationDTO;

import java.math.BigDecimal;
import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "Response containing calculated duty amount and transaction details")
public record CalculateDutyResponse(
    @Schema(description = "Generated transaction ID for this calculation", example = "67890")
    Integer transactionId,
    
    @Schema(description = "ID of the tariff used in calculation", example = "12345")
    String tariffId,
    
    @Schema(description = "Total calculated duty amount", example = "1250.75")
    BigDecimal total
){}
