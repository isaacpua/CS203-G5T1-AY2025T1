package com.tariff.tariff_backend.model;

import java.math.BigDecimal;
import java.util.List;

import com.tariff.tariff_backend.service.RateParser.RateKind;

public record TariffComputeResponse(
    BigDecimal totalDuty,
    BigDecimal totalValue,
    List<BreakdownLine> breakdown
) {
    public static record BreakdownLine( //I need this so in the frontend itll be easier, itll breakdown the composite stuff easier
        RateKind kind,
        BigDecimal dutyAmount,
        BigDecimal adValorem,
        BigDecimal specificPerUnit,
        String unit,
        String qualifier
    ){}
} 