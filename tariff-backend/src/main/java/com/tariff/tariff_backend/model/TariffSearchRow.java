package com.tariff.tariff_backend.model;

public record TariffSearchRow(
    Integer id,
    Integer tariffid,
    String descriptionwcountry,
    String name,
    String overallKind,
    boolean isFree
) {}
