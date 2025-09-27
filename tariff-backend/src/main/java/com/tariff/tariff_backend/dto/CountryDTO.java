package com.tariff.tariff_backend.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
@Schema(description = "Country data transfer object for API responses")
public class CountryDTO {
    
    @Schema(description = "Unique country identifier", example = "840")
    private Integer countryId;
    
    @Schema(description = "ISO 2-letter country code", example = "US")
    private String iso2;
    
    @Schema(description = "Full country name", example = "United States")
    private String name;
}
