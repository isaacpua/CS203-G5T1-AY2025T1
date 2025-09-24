package com.tariff.tariff_backend.model.dashboard;

import java.math.BigDecimal;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class TariffPatchDTO {
    // Expose all fields that users can update from the dashboard
    private Integer tariffid;
    private String descriptionwcountry;
    private Integer partnercountry;
    private Integer reportercountry;
    private String unitname;
    private String category;
    private BigDecimal advalorem;
    private BigDecimal specificperunit;
}