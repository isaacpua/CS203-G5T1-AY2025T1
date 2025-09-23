package com.tariff.tariff_backend.dto.CalculationDTO;

import java.math.BigDecimal;

public record CalculateDutyResponse(
    Integer transactionId,
    Integer tariffId,
    BigDecimal total
){}
