package com.tariff.tariff_backend.dto;

import java.math.BigDecimal;
import java.time.LocalDate;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "Tariff data transfer object for dashboard operations")
public class TariffPatchDTO {
    
    @Schema(description = "Unique tariff identifier", example = "12345")
    @NotNull
    private String tariffId;
    
    @Schema(description = "Product description including country-specific details", example = "Wheat flour - Canada to USA")
    @NotNull
    private String descriptionwcountry;
    
    @Schema(description = "Partner/source country name", example = "Canada")
    @NotNull
    private String partnerCountry;
    
    @Schema(description = "Reporter/destination country name", example = "United States")
    @NotNull
    private String reporterCountry;
    
    @Schema(description = "Unit of measurement for the tariff", example = "kg")
    private String unitname;
    
    @Schema(description = "Product category classification", example = "Agricultural Products")
    @NotNull
    private String category;
    
    @Schema(description = "Ad valorem tariff rate as percentage", example = "12.50")
    private BigDecimal adValorem;
    
    @Schema(description = "Specific tariff rate per unit", example = "0.75")
    private BigDecimal specificPerUnit;

    @Schema(description = "Effective date", example = "2024-01-01")
    private LocalDate effectivedate;

    @Schema(description = "Expiry date", example = "2024-12-31")
    private LocalDate expirydate;

    @Schema(description = "Data source", example = "Government Gazette")
    private String datasource;

    @Schema(description = "year sourced for the tariff data", example = "2002")
    @NotNull
    private Integer year;
}
