package com.tariff.tariff_backend.model.history;

import com.fasterxml.jackson.annotation.JsonFormat;
import io.swagger.v3.oas.annotations.media.Schema;
import java.time.LocalDate;
import java.util.List;

@Schema(description = "Historical tariff data response with time series information")
public class HistoricalResponse {
    
    @Schema(description = "Reporter/destination country", example = "United States")
    private String reporter;
    
    @Schema(description = "Partner/source country", example = "China")
    private String partner;
    
    @Schema(description = "Trade item/product code", example = "010121")
    private String itemCode;
    
    @Schema(description = "Unit of measurement for tariff values")
    private Unit unit;
    
    @Schema(description = "Data frequency", example = "MONTHLY", defaultValue = "MONTHLY")
    private String frequency = "MONTHLY";

    @JsonFormat(pattern = "yyyy-MM-dd")
    @Schema(description = "Start date of the time series", example = "2020-01-01")
    private LocalDate startDate;

    @JsonFormat(pattern = "yyyy-MM-dd")
    @Schema(description = "End date of the time series", example = "2023-12-31")
    private LocalDate endDate;

    @Schema(description = "List of historical data points", required = true)
    private List<HistoricalPoint> points;

    public String getReporter() { return reporter; }
    public void setReporter(String reporter) { this.reporter = reporter; }
    public String getPartner() { return partner; }
    public void setPartner(String partner) { this.partner = partner; }
    public String getItemCode() { return itemCode; }
    public void setItemCode(String itemCode) { this.itemCode = itemCode; }
    public Unit getUnit() { return unit; }
    public void setUnit(Unit unit) { this.unit = unit; }
    public String getFrequency() { return frequency; }
    public void setFrequency(String frequency) { this.frequency = frequency; }
    public LocalDate getStartDate() { return startDate; }
    public void setStartDate(LocalDate startDate) { this.startDate = startDate; }
    public LocalDate getEndDate() { return endDate; }
    public void setEndDate(LocalDate endDate) { this.endDate = endDate; }
    public List<HistoricalPoint> getPoints() { return points; }
    public void setPoints(List<HistoricalPoint> points) { this.points = points; }
}
