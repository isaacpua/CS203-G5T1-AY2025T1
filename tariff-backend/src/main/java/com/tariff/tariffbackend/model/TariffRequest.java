package com.tariff.tariffbackend.model;

import java.math.BigDecimal;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class TariffRequest {

    private String fromCountry;
    private String toCountry;
    private String productCategory;
    private BigDecimal value;

}