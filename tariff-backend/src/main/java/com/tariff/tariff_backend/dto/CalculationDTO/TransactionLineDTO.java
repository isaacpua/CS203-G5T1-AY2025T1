package com.tariff.tariff_backend.dto.CalculationDTO;

import java.time.Instant;
import java.util.Map;

import io.swagger.v3.oas.annotations.media.Schema;

public record TransactionLineDTO(

    @Schema(description =  "Time Tariff was created")
    Instant created_at,

    @Schema(description = "Snapshot of the tariff calculation at the time of transaction")
    Map<String,Object> snapshot
) {}
