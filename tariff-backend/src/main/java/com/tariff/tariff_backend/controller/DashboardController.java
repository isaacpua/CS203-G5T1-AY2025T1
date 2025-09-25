package com.tariff.tariff_backend.controller;

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

import com.tariff.tariff_backend.model.dashboard.DashboardMetrics;
import com.tariff.tariff_backend.model.dashboard.DashboardResponse;
import com.tariff.tariff_backend.model.dashboard.TariffPatchDTO;
import com.tariff.tariff_backend.service.DashboardService;
import com.tariff.tariff_backend.service.JwtService;

@RestController
@RequestMapping("/api/v1/dashboard")
@CrossOrigin(origins = "http://localhost:5173")
public class DashboardController {

    private final DashboardService dashboardService;
    private JwtService jwtService;

    public DashboardController(DashboardService dashboardService, JwtService jwtService) {
        this.dashboardService = dashboardService;
        this.jwtService = jwtService;
    }

    @PostMapping("/tariffs")
    public ResponseEntity<?> createTariff(@RequestHeader("Authorization") String authHeader, @RequestBody TariffPatchDTO request) {
        if (authHeader == null || !jwtService.hasRole(jwtService.getTokenFromHeader(authHeader), "admin")) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body("You do not have enough permissions.");
        }
        DashboardResponse dResponse = dashboardService.createTariff(request);
        if (!dResponse.getSuccess()) {
            return ResponseEntity.badRequest().body(dResponse);
        }
        return ResponseEntity.ok(dResponse);
    }

    @PatchMapping("/tariffs/{tariffid}")
    public ResponseEntity<?> updateTariff(@RequestHeader("Authorization") String authHeader, @PathVariable Integer tariffid, @RequestBody TariffPatchDTO patchDTO) {
        if (authHeader == null || !jwtService.hasRole(jwtService.getTokenFromHeader(authHeader), "admin")) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body("You do not have enough permissions.");
        }
        DashboardResponse dResponse = dashboardService.updateTariff(tariffid, patchDTO);
        if (!dResponse.getSuccess()) {
            return ResponseEntity.badRequest().body(dResponse);
        }
        return ResponseEntity.ok(dResponse);
    }

    @DeleteMapping("/tariffs/{tariffid}")
    public ResponseEntity<?> deleteTariff(@RequestHeader("Authorization") String authHeader, @PathVariable Integer tariffid) {
        if (authHeader == null || !jwtService.hasRole(jwtService.getTokenFromHeader(authHeader), "admin")) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body("You do not have enough permissions.");
        }
        DashboardResponse dResponse = dashboardService.deleteTariff(tariffid);
        if (!dResponse.getSuccess()) {
            return ResponseEntity.badRequest().body(dResponse);
        }
        return ResponseEntity.ok(dResponse);
    }

    @GetMapping("/tariffs")
    public ResponseEntity<DashboardMetrics> getTariffs(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size,
            @RequestParam(required = false) Integer tariffid,
            @RequestParam(name = "q", required = false) String descriptionQuery) {

        int safePage = Math.max(page, 0);
        int safeSize = size > 0 ? size : 50;
        Pageable pageable = PageRequest.of(safePage, safeSize, Sort.by("tariffid").ascending());
        String trimmedQuery = descriptionQuery != null ? descriptionQuery.trim() : null;
        DashboardMetrics metrics = dashboardService.getTariffs(tariffid, trimmedQuery, pageable);
        return ResponseEntity.ok(metrics);
    }
}