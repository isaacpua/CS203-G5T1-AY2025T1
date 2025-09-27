// src/main/java/com/tariff/tariff_backend/controller/TariffBrowseController.java
package com.tariff.tariff_backend.controller;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import com.tariff.tariff_backend.dto.CountryDTO;
import com.tariff.tariff_backend.dto.CalculationDTO.CalculateDutyRequest;
import com.tariff.tariff_backend.dto.CalculationDTO.CalculateDutyResponse;
import com.tariff.tariff_backend.model.tariffs_new.Tariff;
import com.tariff.tariff_backend.repository.TariffRepo;
import com.tariff.tariff_backend.service.CalculationService;

@RestController
@RequestMapping("/api/v1/tariffs")
public class TariffBrowseController {

    // Fill the FROM dropdown (distinct partner countries present in tariffs)
    private final TariffRepo repo;
    private final CalculationService calcService;

    public TariffBrowseController(TariffRepo repo, CalculationService calcService) {
        this.repo = repo;
        this.calcService = calcService;
    }

    @GetMapping("/countries/partners")
    public List<CountryDTO> fromCountries(@RequestParam(required = false) Integer toId) {
        if (toId != null) {
            return repo.availableFromByTo(toId);
        }
        return repo.availableFrom();
    }

    @GetMapping("/countries/reporters")
    public List<CountryDTO> toCountries(@RequestParam(required = false) Integer fromId) {
        return repo.availableTo(fromId);
    }

    @GetMapping("/search")
    public Map<String, Object> search(
            @RequestParam(required = false) Integer fromId,
            @RequestParam(required = false) Integer toId,
            @RequestParam(required = false) String q,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {

        String query = (q == null || q.trim().isEmpty()) ? null : q.trim();
        Page<Tariff> result = repo.searchNative(fromId, toId, query, PageRequest.of(page, size));

        Map<String, Object> response = new HashMap<>();
        response.put("content", result.getContent());
        response.put("number", result.getNumber());
        response.put("size", result.getSize());
        response.put("totalPages", result.getTotalPages());
        response.put("totalElements", result.getTotalElements());
        response.put("last", result.isLast());

        return response;
    }

    @PostMapping("/calc")
    public ResponseEntity<CalculateDutyResponse> calculate(@RequestBody CalculateDutyRequest req) {
        return ResponseEntity.ok(calcService.calculateAndStore(req));
    }
}
