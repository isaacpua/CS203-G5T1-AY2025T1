package com.tariff.tariff_backend.model;

import java.math.BigDecimal;
import java.util.Map;

//take in from frontend, what info i need from the user to calc

public record TariffComputeRequest(
    BigDecimal declaredValue,
    BigDecimal quantity,
    String uom,
    Map<String, BigDecimal> declaredByQualifier
) {}
