package com.tariff.tariff_backend.dto;

import java.math.BigDecimal;

public record CalculateDutyResponse(
    Integer transactionId,
    Integer tariffId,
    BigDecimal adValoremPart,
    BigDecimal specificPart,
    BigDecimal total
){}
