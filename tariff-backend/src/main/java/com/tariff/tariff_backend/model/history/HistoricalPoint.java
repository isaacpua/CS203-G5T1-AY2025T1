package com.tariff.tariff_backend.model.history;

import com.fasterxml.jackson.annotation.JsonFormat;
import java.time.LocalDate;

public class HistoricalPoint {
    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate date;
    private double value;

    public HistoricalPoint() {}
    public HistoricalPoint(LocalDate date, double value) { this.date = date; this.value = value; }

    public LocalDate getDate() { return date; }
    public void setDate(LocalDate date) { this.date = date; }
    public double getValue() { return value; }
    public void setValue(double value) { this.value = value; }
}
