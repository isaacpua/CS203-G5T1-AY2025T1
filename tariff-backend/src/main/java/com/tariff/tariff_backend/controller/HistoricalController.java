package com.tariff.tariff_backend.controller;

import com.tariff.tariff_backend.model.history.HistoryPreset;
import com.tariff.tariff_backend.model.history.HistoricalResponse;
import com.tariff.tariff_backend.model.history.Unit;
import com.tariff.tariff_backend.service.HistoricalService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/api/v1/tariffs")
@CrossOrigin(origins = {"http://localhost:5173", "http://localhost:5174"}, allowCredentials = "true")
@Tag(name = "Historical Tariff Explorer")
public class HistoricalController {

    private final HistoricalService service;

    public HistoricalController(HistoricalService service) {
        this.service = service;
    }

    // GET /api/v1/tariffs/history?reporter=&partner=&itemCode=&start=&end=&unit=percent|value
    @GetMapping("/history")
    @Operation(summary = "Get historical tariff series (mock monthly data)")
    public ResponseEntity<HistoricalResponse> history(
            @RequestParam(required = false) String reporter,
            @RequestParam(required = false) String partner,
            @RequestParam(required = false) String itemCode,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end,
            @RequestParam(required = false, defaultValue = "percent") String unit
    ) {
        return ResponseEntity.ok(
            service.getHistory(reporter, partner, itemCode, start, end, Unit.fromString(unit))
        );
    }

    // GET /api/v1/tariffs/recommendations -> [{title, reporter, partner, itemCode}]
    @GetMapping("/recommendations")
    @Operation(summary = "Return recommended presets used by the UI")
    public ResponseEntity<List<HistoryPreset>> recommendations() {
        return ResponseEntity.ok(service.presets());
    }
}
