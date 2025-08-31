package com.tariff.tariff_backend.controller;


import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.tariff.tariff_backend.model.TariffComputeRequest;
import com.tariff.tariff_backend.model.TariffComputeResponse;
import com.tariff.tariff_backend.model.TariffSearchRow;
import com.tariff.tariff_backend.service.TariffService;

@RestController
@RequestMapping("/api/v1/tariffs")
@CrossOrigin(origins = "http://localhost:5173")
public class TariffController {

    private final TariffService tariffService;

    public TariffController(TariffService tariffService) {
        this.tariffService = tariffService;
    }

    @GetMapping("/search")
    public Page<TariffSearchRow> search(
        @RequestParam(required = false) Integer id,
        @RequestParam(required = false) Integer hts8,
        @RequestParam(required = false) String q,
        @PageableDefault(size = 10, sort = "hts8", direction = Sort.Direction.ASC) Pageable pageable //set it to default
    ) {
        return tariffService.searchTariffs(id, hts8, q, pageable);
    }

    @PostMapping("/compute")
    public TariffComputeResponse compute(
        @RequestParam Integer id,
        @RequestBody TariffComputeRequest req
    ) {
        return tariffService.computeTariff(id ,req);
    }
    

}