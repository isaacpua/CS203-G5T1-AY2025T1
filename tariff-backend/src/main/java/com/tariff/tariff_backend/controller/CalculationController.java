package com.tariff.tariff_backend.controller;

import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.tariff.tariff_backend.dto.CalculationDTO.CalculateDutyRequest;
import com.tariff.tariff_backend.dto.CalculationDTO.CalculateDutyResponse;
import com.tariff.tariff_backend.service.CalculationService;


import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;


@RestController
@RequestMapping("/api/v1/tariffs/calc")
@CrossOrigin(origins = "http://localhost:5173")
public class CalculationController {
    private final CalculationService service;

    public CalculationController(CalculationService service){
        this.service = service;
    }

    @PostMapping
    public ResponseEntity<CalculateDutyResponse> calculate(@RequestBody CalculateDutyRequest req) {
        return ResponseEntity.ok(service.calculateAndStore(req));
    }
    
}
