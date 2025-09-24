package com.tariff.tariff_backend.model;

import java.math.BigDecimal;

public record TariffSearchRow(
    Integer tariffid,
    String descriptionwcountry,
    String overallKind,
    boolean isFree,
    Integer partnercountry,
    Integer reportercountry,
    String unitname,
    String category,
    BigDecimal advalorem,
    BigDecimal specificperunit
) {}