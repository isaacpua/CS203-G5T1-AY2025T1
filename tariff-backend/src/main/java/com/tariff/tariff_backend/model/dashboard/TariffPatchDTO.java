package com.tariff.tariff_backend.model.dashboard;

import java.math.BigDecimal;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "Tariff data transfer object for dashboard operations")
public class TariffPatchDTO {
    
    @Schema(description = "Unique tariff identifier", example = "12345")
    private Integer tariffId;
    
    @Schema(description = "Product description including country-specific details", example = "Wheat flour - Canada to USA")
    private String descriptionwcountry;
    
    @Schema(description = "Partner/source country name", example = "Canada")
    private String partnerCountry;
    
    @Schema(description = "Reporter/destination country name", example = "United States")
    private String reporterCountry;
    
    @Schema(description = "Unit of measurement for the tariff", example = "kg")
    private String unitname;
    
    @Schema(description = "Product category classification", example = "Agricultural Products")
    private String category;
    
    @Schema(description = "Ad valorem tariff rate as percentage", example = "12.50")
    private BigDecimal adValorem;
    
    @Schema(description = "Specific tariff rate per unit", example = "0.75")
    private BigDecimal specificPerUnit;
}
