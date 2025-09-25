package com.tariff.tariff_backend.model.dashboard;

import java.math.BigDecimal;


import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class TariffPatchDTO {
    // Default fields for responses
    private Integer tariffId;
    private String descriptionwcountry;
    private String partnerCountry;
    private String reporterCountry;
    private String unitname;
    private String category;
    private BigDecimal adValorem;
    private BigDecimal specificPerUnit;
}