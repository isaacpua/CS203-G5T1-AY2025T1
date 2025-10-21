package com.tariff.tariff_backend.dto.CalculationDTO;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.Map;

import io.swagger.v3.oas.annotations.media.Schema;

public record TransactionLineDTO(
    @Schema(description = "ID of the tariff used in calculation", example = "12345")
    Integer tariffId,
    
    @Schema(description = "Total calculated duty amount", example = "1250.75")
    BigDecimal total,

    @Schema(description =  "Time Tariff was created")
    Instant created_at,

    @Schema(description = "Description of tariff" )
    String description,

    @Schema(description = "Snapshot of the tariff calculation at the time of transaction")
    Map<String,Object> snapshot
) {}
