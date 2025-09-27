package com.tariff.tariff_backend.model.tariffs_new;

import java.math.BigDecimal;
import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "Tariff search result record with complete tariff information")
public record TariffSearchRow(
    @Schema(description = "Unique tariff identifier", example = "12345")
    Integer tariffId,
    
    @Schema(description = "Product description with country context", example = "Live horses - from Canada")
    String descriptionwcountry,
    
    @Schema(description = "Partner/source country information")
    Country partnerCountry,
    
    @Schema(description = "Reporter/destination country information")
    Country reporterCountry,
    
    @Schema(description = "Unit of measurement", example = "kg")
    String unitname,
    
    @Schema(description = "Product category", example = "Live Animals")
    String category,
    
    @Schema(description = "Ad valorem tariff rate (percentage)", example = "12.5")
    BigDecimal advalorem,
    
    @Schema(description = "Specific tariff rate per unit", example = "0.75")
    BigDecimal specificperunit
) {}
