package com.tariff.tariff_backend.dto.CalculationDTO;

import java.math.BigDecimal;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotNull;

@Schema(description = "Request for calculating customs duty on a tariff")
public record CalculateDutyRequest( 
    @Schema(description = "ID of the tariff to calculate duty for", example = "12345", required = true)
    @NotNull
    String tariffId,
    
    @Schema(description = "Customs value of goods (CIF value for ad valorem calculations)", 
            example = "10000.00", required = true)
    BigDecimal customsValue,
    
    @Schema(description = "Quantity of goods for specific duty calculations", 
            example = "500.00", required = true)
    BigDecimal quantity,

    @NotNull
    Boolean save //whether to save the current transaction or not
){}
