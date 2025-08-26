package com.tariff.tariff_backend.model;

import java.math.BigDecimal;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
public class TariffResponse {

    private BigDecimal calculatedTariff;
    private BigDecimal totalValue;

}