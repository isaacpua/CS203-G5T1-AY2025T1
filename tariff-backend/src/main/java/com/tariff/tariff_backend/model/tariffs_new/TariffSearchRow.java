package com.tariff.tariff_backend.model.tariffs_new;

import java.math.BigDecimal;

public record TariffSearchRow(
    Integer tariffId,
    String descriptionwcountry,
    Country partnerCountry,
    Country reporterCountry,
    String unitname,
    String category,
    BigDecimal advalorem,
    BigDecimal specificperunit
) {}
