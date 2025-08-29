package com.tariff.tariff_backend.model.dashboard;
import lombok.Data;
import lombok.AllArgsConstructor;

@Data
@AllArgsConstructor
public class TariffPatchDTO {
    // Only expose the fields users can update
    private Integer hts8;
    private String briefDescription;
    private String mfnTextRate;
    // No internal fields exposed!
}
