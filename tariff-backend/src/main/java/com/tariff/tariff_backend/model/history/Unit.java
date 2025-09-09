package com.tariff.tariff_backend.model.history;

public enum Unit {
    PERCENT, VALUE;

    public static Unit fromString(String s) {
        if (s == null) return PERCENT;
        try { return Unit.valueOf(s.trim().toUpperCase()); }
        catch (IllegalArgumentException ex) { return PERCENT; }
    }
}
