package com.tariff.tariff_backend.controller;

import com.tariff.tariff_backend.model.history.HistoryPreset;
import com.tariff.tariff_backend.model.history.HistoricalResponse;
import com.tariff.tariff_backend.model.history.Unit;
import com.tariff.tariff_backend.service.HistoricalService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/api/v1/tariffs")
@CrossOrigin(origins = {"http://localhost:5173", "http://localhost:5174"}, allowCredentials = "true")
@Tag(name = "Tariff Historical Explorer", description = "Historical tariff data exploration and analysis")
public class HistoricalController {

    private final HistoricalService service;

    public HistoricalController(HistoricalService service) {
        this.service = service;
    }

    @Operation(
        summary = "Get historical tariff time series",
        description = "Retrieves historical tariff data with optional filtering by reporter, partner, item code, and date range. Returns mock monthly data for analysis and visualization."
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Historical tariff data retrieved successfully",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = HistoricalResponse.class)))
    })
    @GetMapping("/history")
    public ResponseEntity<HistoricalResponse> history(
            @Parameter(description = "Reporting country/region code or name", example = "USA")
            @RequestParam(required = false) String reporter,
            @Parameter(description = "Partner country/region code or name", example = "CHN")
            @RequestParam(required = false) String partner,
            @Parameter(description = "Trade item/product code (HS code or similar)", example = "010121")
            @RequestParam(required = false) String itemCode,
            @Parameter(description = "Start date for historical data (ISO date format)", example = "2020-01-01")
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
            @Parameter(description = "End date for historical data (ISO date format)", example = "2023-12-31")
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end,
            @Parameter(description = "Unit of measurement for tariff data", 
                      schema = @Schema(allowableValues = {"percent", "value"}), example = "percent")
            @RequestParam(required = false, defaultValue = "percent") String unit
    ) {
        return ResponseEntity.ok(
            service.getHistory(reporter, partner, itemCode, start, end, Unit.fromString(unit))
        );
    }

    @Operation(
        summary = "Get recommended tariff presets",
        description = "Returns a list of predefined tariff analysis presets commonly used by the UI. These presets contain pre-configured combinations of reporter, partner, and item codes for quick analysis."
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Preset recommendations retrieved successfully",
            content = @Content(mediaType = "application/json", 
                schema = @Schema(type = "array", implementation = HistoryPreset.class)))
    })
    @GetMapping("/recommendations")
    public ResponseEntity<List<HistoryPreset>> recommendations() {
        return ResponseEntity.ok(service.presets());
    }
}
