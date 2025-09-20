package com.tariff.tariff_backend.model.tariffs_old;

import java.math.BigDecimal;
import java.util.Map;

//take in from frontend, what info i need from the user to calc

public record TariffComputeRequest(
    BigDecimal declaredValue,
    BigDecimal quantity,
    String uom,
    Map<String, BigDecimal> declaredByQualifier
) {}
