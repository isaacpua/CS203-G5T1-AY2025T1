package com.tariff.tariff_backend.model.history;

import com.fasterxml.jackson.annotation.JsonFormat;
import io.swagger.v3.oas.annotations.media.Schema;
import java.time.LocalDate;

@Schema(description = "Single data point in historical tariff time series")
public class HistoricalPoint {
    
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Schema(description = "Date of the data point", example = "2023-06-01", required = true)
    private LocalDate date;
    
    @Schema(description = "Tariff value at this date (percentage or absolute value)", example = "15.75", required = true)
    private double value;

    public HistoricalPoint() {}
    public HistoricalPoint(LocalDate date, double value) { this.date = date; this.value = value; }

    public LocalDate getDate() { return date; }
    public void setDate(LocalDate date) { this.date = date; }
    public double getValue() { return value; }
    public void setValue(double value) { this.value = value; }
}
