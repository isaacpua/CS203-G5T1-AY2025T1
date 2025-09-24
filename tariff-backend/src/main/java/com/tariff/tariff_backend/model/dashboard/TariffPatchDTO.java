package com.tariff.tariff_backend.model.dashboard;
import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class TariffPatchDTO {
    // Only expose the fields users can update
    private Integer tariffid;
    private String descriptionwcountry;

    // Add getters for new fields
    public Integer getTariffid() { return tariffid; }
    public String getDescriptionwcountry() { return descriptionwcountry; }

    // Optionally, add setters if needed
    public void setTariffid(Integer tariffid) { this.tariffid = tariffid; }
    public void setDescriptionwcountry(String descriptionwcountry) { this.descriptionwcountry = descriptionwcountry; }
}