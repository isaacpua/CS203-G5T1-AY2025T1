package com.tariff.tariff_backend.service;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.Random;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.model.history.HistoricalPoint;
import com.tariff.tariff_backend.model.history.HistoricalResponse;
import com.tariff.tariff_backend.model.history.HistoryPreset;
import com.tariff.tariff_backend.model.history.Unit;

@Service
public class HistoricalService {

    public HistoricalResponse getHistory(
            String reporter, String partner, String itemCode,
            LocalDate start, LocalDate end, Unit unit
    ) {
        LocalDate s = (start == null) ? LocalDate.now().minusYears(3).withDayOfMonth(1) : start.withDayOfMonth(1);
        LocalDate e = (end   == null) ? LocalDate.now().withDayOfMonth(1) : end.withDayOfMonth(1);
        if (e.isBefore(s)) { LocalDate tmp = s; s = e; e = tmp; }

        List<LocalDate> months = monthRange(s, e);

        long seed = Objects.hash(safe(reporter), safe(partner), safe(itemCode), s, e, unit);
        Random r = new Random(seed);

        double base  = (unit == Unit.PERCENT) ? 5 + r.nextDouble() * 10 : 50 + r.nextDouble() * 150;
        double drift = (unit == Unit.PERCENT) ? (r.nextDouble() - 0.5) * 0.06 : (r.nextDouble() - 0.5) * 1.0;

        List<HistoricalPoint> points = new ArrayList<>();
        int i = 0;
        for (LocalDate m : months) {
            double wave  = Math.sin(i / 3.0) * ((unit == Unit.PERCENT) ? 2.5 : 12.0);
            double noise = (r.nextDouble() - 0.5) * ((unit == Unit.PERCENT) ? 0.8 : 3.0);
            double val   = base + i * drift + wave + noise;

            if (unit == Unit.PERCENT) val = Math.max(0, Math.min(100, val));
            val = Math.round(val * 100.0) / 100.0;

            points.add(new HistoricalPoint(m, val));
            i++;
        }

        HistoricalResponse resp = new HistoricalResponse();
        resp.setReporter(reporter);
        resp.setPartner(partner);
        resp.setItemCode(itemCode);
        resp.setUnit(unit);
        resp.setStartDate(months.isEmpty() ? s : months.get(0));
        resp.setEndDate(months.isEmpty() ? e : months.get(months.size()-1));
        resp.setPoints(points);
        return resp;
    }

    public List<HistoryPreset> presets() {
        return Arrays.asList(
            new HistoryPreset("TW→SG Semiconductors", "Taiwan", "Singapore", "8471"),
            new HistoryPreset("US→EU Steel", "United States", "European Union", "7208")
        );
    }

    private static String safe(String s) { return s == null ? "" : s.trim().toLowerCase(); }

    private static List<LocalDate> monthRange(LocalDate startInclusive, LocalDate endInclusive) {
        long months = ChronoUnit.MONTHS.between(startInclusive, endInclusive);
        if (months < 0) return Collections.emptyList();
        return Stream.iterate(startInclusive, d -> d.plusMonths(1))
                     .limit(months + 1)
                     .collect(Collectors.toList());
    }
}
