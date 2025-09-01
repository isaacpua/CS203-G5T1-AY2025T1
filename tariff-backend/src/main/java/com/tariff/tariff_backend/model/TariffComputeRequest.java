package com.tariff.tariff_backend.model;

import java.math.BigDecimal;

public record TariffComputeRequest(
    BigDecimal declaredValue,
    BigDecimal quantity,
    String uom
) {}
