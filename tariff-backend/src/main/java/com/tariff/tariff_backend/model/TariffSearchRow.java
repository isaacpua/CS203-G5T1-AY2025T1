package com.tariff.tariff_backend.model;

import java.math.BigDecimal;

import com.tariff.tariff_backend.model.tariffs_new.Country;

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
