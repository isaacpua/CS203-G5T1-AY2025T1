package com.tariff.tariff_backend.model.dashboard;

import java.math.BigDecimal;

import com.tariff.tariff_backend.model.tariffs_new.Country;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class TariffPatchDTO {
    // Expose all fields that users can update from the dashboard
    private String descriptionwcountry;
    private Country partnerCountry;
    private Country reporterCountry;
    private String unitname;
    private String category;
    private BigDecimal adValorem;
    private BigDecimal specificPerUnit;
}