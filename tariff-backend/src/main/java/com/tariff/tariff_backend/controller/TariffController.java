package com.tariff.tariff_backend.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.tariff.tariff_backend.model.TariffRequest;
import com.tariff.tariff_backend.model.TariffResponse;
import com.tariff.tariff_backend.service.TariffService;

@RestController
@RequestMapping("/api/v1/tariffs")
@CrossOrigin(origins = "http://localhost:5173")
public class TariffController {

    private final TariffService tariffService;

    @Autowired
    public TariffController(TariffService tariffService) {
        this.tariffService = tariffService;
    }

    @PostMapping("/calculate")
    public TariffResponse calculate(@RequestBody TariffRequest request) {
        return tariffService.calculateTariff(request);
    }
}