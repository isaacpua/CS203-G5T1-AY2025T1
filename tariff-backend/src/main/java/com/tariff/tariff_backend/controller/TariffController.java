package com.tariff.tariff_backend.controller;

import java.math.BigDecimal;


import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.tariff.tariff_backend.model.tariffs_new.Country;
import com.tariff.tariff_backend.model.tariffs_new.TariffSearchRow;
import com.tariff.tariff_backend.service.TariffService;



@RestController
@RequestMapping("/api/v1/tariffs")
@CrossOrigin(origins = {"http://localhost:5173", "http://localhost:5174"})
public class TariffController {

    private final TariffService tariffService;

    public TariffController(TariffService tariffService) {
        this.tariffService = tariffService;
    }

    @GetMapping("/search")
    public Page<TariffSearchRow> search(
        @RequestParam(required = false) Integer tariffId,
        @RequestParam(required = false) String descriptionwcountry,
        @RequestParam(required = false) Country partnerCountry,
        @RequestParam(required = false) Country reporterCountry,
        @RequestParam(required = false) String unitname,
        @RequestParam(required = false) String category,
        @RequestParam(required = false) BigDecimal advalorem,
        @RequestParam(required = false) BigDecimal specificperunit,
        @PageableDefault(size = 10, sort = "tariffId", direction = Sort.Direction.ASC) Pageable pageable
    ) {
        Page<TariffSearchRow> results = tariffService.searchTariffs(
            tariffId, descriptionwcountry, partnerCountry, reporterCountry,
            unitname, category, advalorem, specificperunit, pageable
        );


        return results;
    }
}