package com.tariff.tariff_backend.model;

import java.math.BigDecimal;

public record TariffSearchRow(
    Integer id,
    Integer tariffid,
    String descriptionwcountry,
    String name,
    String overallKind,
    boolean isFree,
    Integer partnercountry,
    Integer reportercountry,
    Integer unitid,
    String category,
    BigDecimal advalorem,
    BigDecimal specificperunit,
    BigDecimal ad_valorem,
    BigDecimal specific_per_unit
) {}
