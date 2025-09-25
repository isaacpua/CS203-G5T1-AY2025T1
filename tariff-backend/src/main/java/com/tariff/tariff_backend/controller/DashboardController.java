package com.tariff.tariff_backend.controller;

import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.tariff.tariff_backend.model.dashboard.DashboardMetrics;
import com.tariff.tariff_backend.model.dashboard.DashboardResponse;
import com.tariff.tariff_backend.model.dashboard.TariffPatchDTO;
import com.tariff.tariff_backend.model.tariffs_new.Tariff;
import com.tariff.tariff_backend.service.DashboardService;

@RestController
@RequestMapping("/api/v1/dashboard")
@CrossOrigin(origins = "http://localhost:5173")
public class DashboardController {

    private final DashboardService dashboardService;

    public DashboardController(DashboardService dashboardService) {
        this.dashboardService = dashboardService;
    }

    @PostMapping("/tariffs")
    public ResponseEntity<?> createTariff(@RequestBody Tariff request) {
        DashboardResponse dResponse = dashboardService.createTariff(request);
        if (!dResponse.getSuccess()) {
            return ResponseEntity.badRequest().body(dResponse);
        }
        return ResponseEntity.ok(dResponse);
    }

    @PatchMapping("/tariffs/{tariffid}")
    public ResponseEntity<?> updateTariff(@PathVariable Integer tariffId, @RequestBody TariffPatchDTO patchDTO) {
        DashboardResponse dResponse = dashboardService.updateTariff(tariffId, patchDTO);
        if (!dResponse.getSuccess()) {
            return ResponseEntity.badRequest().body(dResponse);
        }
        return ResponseEntity.ok(dResponse);
    }

    @DeleteMapping("/tariffs/{tariffid}")
    public ResponseEntity<?> deleteTariff(@PathVariable Integer tariffId) {
        DashboardResponse dResponse = dashboardService.deleteTariff(tariffId);
        if (!dResponse.getSuccess()) {
            return ResponseEntity.badRequest().body(dResponse);
        }
        return ResponseEntity.ok(dResponse);
    }

    @GetMapping("/tariffs")
    public ResponseEntity<DashboardMetrics> getTariffs(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size,
            @RequestParam(required = false) Integer tariffId,
            @RequestParam(name = "q", required = false) String descriptionQuery) {

        int safePage = Math.max(page, 0);
        int safeSize = size > 0 ? size : 50;
        Pageable pageable = PageRequest.of(safePage, safeSize, Sort.by("tariffId").ascending());
        String trimmedQuery = descriptionQuery != null ? descriptionQuery.trim() : null;
        DashboardMetrics metrics = dashboardService.getTariffs(tariffId, trimmedQuery, pageable);
        return ResponseEntity.ok(metrics);
    }
}