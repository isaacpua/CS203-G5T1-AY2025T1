package com.tariff.tariff_backend.dto.CalculationDTO;

import java.math.BigDecimal;
import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "Request for calculating customs duty on a tariff")
public record CalculateDutyRequest( 
    @Schema(description = "ID of the tariff to calculate duty for", example = "12345", required = true)
    Integer tariffId,
    
    @Schema(description = "Customs value of goods (CIF value for ad valorem calculations)", 
            example = "10000.00", required = true)
    BigDecimal customsValue,
    
    @Schema(description = "Quantity of goods for specific duty calculations", 
            example = "500.00", required = true)
    BigDecimal quantity,

    Boolean save //whether to save the current transaction or not
){}
