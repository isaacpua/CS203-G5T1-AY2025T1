package com.tariff.tariff_backend.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.tariff.tariff_backend.model.dashboard.DashboardResponse;
import com.tariff.tariff_backend.model.dashboard.TariffPatchDTO;
import com.tariff.tariff_backend.model.tariffs_old.Tariff;
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

    @PatchMapping("/tariffs/{id}")
    public ResponseEntity<?> updateTariff(@PathVariable Integer id, @RequestBody TariffPatchDTO patchDTO) {
        DashboardResponse dResponse = dashboardService.updateTariff(id, patchDTO);
        if (!dResponse.getSuccess()) {
            return ResponseEntity.badRequest().body(dResponse);
        }
        return ResponseEntity.ok(dResponse);
    }

    @DeleteMapping("/tariffs/{id}")
    public ResponseEntity<?> deleteTariff(@PathVariable Integer id) {
        DashboardResponse dResponse = dashboardService.deleteTariff(id);
        if (!dResponse.getSuccess()) {
            return ResponseEntity.badRequest().body(dResponse);
        }
        return ResponseEntity.ok(dResponse);
    }
}
