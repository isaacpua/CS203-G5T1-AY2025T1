package com.tariff.tariff_backend.dto.CalculationDTO;

import java.math.BigDecimal;

public record CalculateDutyRequest( 
    Integer tariffId,
    BigDecimal customsValue,  // e.g., CIF value for ad valorem
    BigDecimal quantity       // for specific-per-unit
){}