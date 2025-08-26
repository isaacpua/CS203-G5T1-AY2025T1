package com.tariff.tariffbackend.controller;

import com.tariff.tariffbackend.model.TariffRequest;
import com.tariff.tariffbackend.model.TariffResponse;
import com.tariff.tariffbackend.service.TariffService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/tariffs")
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