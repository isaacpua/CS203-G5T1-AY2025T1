package com.tariff.tariff_backend.model.history;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "Predefined tariff analysis configuration for quick access")
public class HistoryPreset {
    
    @Schema(description = "Display title for the preset", example = "US-China Steel Tariffs", required = true)
    private String title;
    
    @Schema(description = "Reporter country for the preset", example = "United States", required = true)
    private String reporter;
    
    @Schema(description = "Partner country for the preset", example = "China", required = true)
    private String partner;
    
    @Schema(description = "Product item code for the preset", example = "720839", required = true)
    private String itemCode;

    public HistoryPreset() {}
    public HistoryPreset(String title, String reporter, String partner, String itemCode) {
        this.title = title; this.reporter = reporter; this.partner = partner; this.itemCode = itemCode;
    }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getReporter() { return reporter; }
    public void setReporter(String reporter) { this.reporter = reporter; }
    public String getPartner() { return partner; }
    public void setPartner(String partner) { this.partner = partner; }
    public String getItemCode() { return itemCode; }
    public void setItemCode(String itemCode) { this.itemCode = itemCode; }
}
