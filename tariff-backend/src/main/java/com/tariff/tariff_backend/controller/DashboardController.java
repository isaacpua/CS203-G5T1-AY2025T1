package com.tariff.tariff_backend.controller;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.tariff.tariff_backend.dto.TariffPatchDTO;
import com.tariff.tariff_backend.model.dashboard.DashboardMetrics;
import com.tariff.tariff_backend.model.dashboard.DashboardResponse;
import com.tariff.tariff_backend.service.DashboardService;
import com.tariff.tariff_backend.service.JwtService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;

@RestController
@RequestMapping("/api/v1/dashboard")
@CrossOrigin(origins = "http://localhost:5173")
@Tag(name = "Tariff Dashboard", description = "Tariff management dashboard operations")
public class DashboardController {

    private final DashboardService dashboardService;
    private JwtService jwtService;

    public DashboardController(DashboardService dashboardService, JwtService jwtService) {
        this.dashboardService = dashboardService;
        this.jwtService = jwtService;
    }

    @Operation(
        summary = "Create new tariff",
        description = "Creates a new tariff entry. Requires admin role.",
        security = @SecurityRequirement(name = "Bearer Authentication")
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Tariff created successfully",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = DashboardResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid tariff data",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = DashboardResponse.class))),
        @ApiResponse(responseCode = "403", description = "Insufficient permissions - admin role required",
            content = @Content(mediaType = "text/plain", schema = @Schema(type = "string", example = "You do not have enough permissions.")))
    })
    @PostMapping("/tariffs")
    public ResponseEntity<?> createTariff(
        @Parameter(description = "Bearer token for admin authentication", required = true)
        @RequestHeader("Authorization") String authHeader,
        @Parameter(description = "Tariff data to create", required = true)
        @RequestBody TariffPatchDTO request) {
        if (authHeader == null || !jwtService.hasRole(jwtService.getTokenFromHeader(authHeader), "admin")) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body("You do not have enough permissions.");
        }
        DashboardResponse dResponse = dashboardService.createTariff(request);
        if (!dResponse.getSuccess()) {
            return ResponseEntity.badRequest().body(dResponse);
        }
        return ResponseEntity.ok(dResponse);
    }

    @Operation(
        summary = "Update existing tariff",
        description = "Updates an existing tariff by ID. Requires admin role.",
        security = @SecurityRequirement(name = "Bearer Authentication")
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Tariff updated successfully",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = DashboardResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid tariff data or tariff not found",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = DashboardResponse.class))),
        @ApiResponse(responseCode = "403", description = "Insufficient permissions - admin role required",
            content = @Content(mediaType = "text/plain", schema = @Schema(type = "string", example = "You do not have enough permissions.")))
    })
    @PatchMapping("/tariffs/{tariffid}")
    public ResponseEntity<?> updateTariff(
        @Parameter(description = "Bearer token for admin authentication", required = true)
        @RequestHeader("Authorization") String authHeader,
        @Parameter(description = "ID of the tariff to update", required = true, example = "1")
        @PathVariable String tariffid,
        @Parameter(description = "Updated tariff data", required = true)
        @RequestBody TariffPatchDTO patchDTO) {
        if (authHeader == null || !jwtService.hasRole(jwtService.getTokenFromHeader(authHeader), "admin")) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body("You do not have enough permissions.");
        }
        DashboardResponse dResponse = dashboardService.updateTariff(tariffid, patchDTO);
        if (!dResponse.getSuccess()) {
            return ResponseEntity.badRequest().body(dResponse);
        }
        return ResponseEntity.ok(dResponse);
    }

    @Operation(
        summary = "Delete tariff",
        description = "Deletes an existing tariff by ID. Requires admin role.",
        security = @SecurityRequirement(name = "Bearer Authentication")
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Tariff deleted successfully",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = DashboardResponse.class))),
        @ApiResponse(responseCode = "400", description = "Tariff not found or cannot be deleted",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = DashboardResponse.class))),
        @ApiResponse(responseCode = "403", description = "Insufficient permissions - admin role required",
            content = @Content(mediaType = "text/plain", schema = @Schema(type = "string", example = "You do not have enough permissions.")))
    })
    @DeleteMapping("/tariffs/{tariffid}")
    public ResponseEntity<?> deleteTariff(
        @Parameter(description = "Bearer token for admin authentication", required = true)
        @RequestHeader("Authorization") String authHeader,
        @Parameter(description = "ID of the tariff to delete", required = true, example = "1")
        @PathVariable String tariffid) {
        if (authHeader == null || !jwtService.hasRole(jwtService.getTokenFromHeader(authHeader), "admin")) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body("You do not have enough permissions.");
        }
        DashboardResponse dResponse = dashboardService.deleteTariff(tariffid);
        if (!dResponse.getSuccess()) {
            return ResponseEntity.badRequest().body(dResponse);
        }
        return ResponseEntity.ok(dResponse);
    }

    @Operation(
        summary = "Get tariffs",
        description = "Retrieves tariffs with optional pagination, filtering by ID, and text search. Use size=0 or negative to get all tariffs without pagination."
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Tariffs retrieved successfully",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = DashboardMetrics.class)))
    })
    @GetMapping("/tariffs")
    public ResponseEntity<?> getTariffs(
            @Parameter(description = "Page number (0-based)", example = "0")
            @RequestParam(defaultValue = "0") int page,
            @Parameter(description = "Number of items per page. Use 0 or negative for all results", example = "50")
            @RequestParam(defaultValue = "50") int size,
            @Parameter(description = "Filter by specific tariff ID", example = "123")
            @RequestParam(name = "tariffid", required = false) String tariffId,
            @Parameter(description = "Search query for tariff description", example = "mobile data")
            @RequestParam(name = "q", required = false) String descriptionQuery) {
        
        // Get all tariff data
        if (size <= 0) {
            List<TariffPatchDTO> allTariffs = dashboardService.getAllTariffs();
            Map<String, List<TariffPatchDTO>> response = new HashMap<>();
            response.put("tariffs", allTariffs);
            return ResponseEntity.ok(response);
        }
        int safePage = Math.max(page, 0);
        int safeSize = size > 0 ? size : 50;
        Pageable pageable = PageRequest.of(safePage, safeSize, Sort.by("tariffId").ascending());
        String trimmedQuery = descriptionQuery != null ? descriptionQuery.trim() : null;
        DashboardMetrics metrics = dashboardService.getTariffs(tariffId, trimmedQuery, pageable);
        return ResponseEntity.ok(metrics);
    }
}
