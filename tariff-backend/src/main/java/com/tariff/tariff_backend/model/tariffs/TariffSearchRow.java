package com.tariff.tariff_backend.model.tariffs;

public record TariffSearchRow( //This is a DTO. So for eg, if your Tariff entity got more data right, this will just take what you need and nothing else so u dont expose sus information
    Integer id,
    Integer hts8,
    String briefDescription,
    String mfnTextRate,
    String overallKind, //from RateParser
    boolean isFree      //from RateParser
) {}
