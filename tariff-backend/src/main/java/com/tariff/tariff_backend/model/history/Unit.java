package com.tariff.tariff_backend.model.history;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "Unit of measurement for tariff values")
public enum Unit {
    @Schema(description = "Tariff as percentage (ad valorem)")
    PERCENT, 
    
    @Schema(description = "Tariff as absolute value (specific duty)")
    VALUE;

    public static Unit fromString(String s) {
        if (s == null) return PERCENT;
        try { return Unit.valueOf(s.trim().toUpperCase()); }
        catch (IllegalArgumentException ex) { return PERCENT; }
    }
}
