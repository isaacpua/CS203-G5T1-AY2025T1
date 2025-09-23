package com.tariff.tariff_backend.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class CountryDTO {
    private Integer countryId;
    private String iso2;
    private String name;
}