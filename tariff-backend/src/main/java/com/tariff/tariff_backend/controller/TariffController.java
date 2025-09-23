package com.tariff.tariff_backend.controller;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.tariff.tariff_backend.model.Tariff;
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
        @RequestParam(required = false) Integer tariffid,
        @RequestParam(required = false) String descriptionwcountry,
        @RequestParam(required = false) Integer partnercountry,
        @RequestParam(required = false) Integer reportercountry,
        @RequestParam(required = false) Integer unitid,
        @RequestParam(required = false) String name,
        @RequestParam(required = false) String category,
        @RequestParam(required = false) Double advalorem,
        @RequestParam(required = false) Double specificperunit,
        @RequestParam(required = false) Integer id,
        @PageableDefault(size = 10, sort = "tariffid", direction = Sort.Direction.ASC) Pageable pageable
    ) {
        return tariffService.searchTariffs(
            tariffid, descriptionwcountry, partnercountry, reportercountry,
            unitid, name, category, advalorem, specificperunit, id, pageable
        );
    }

    @PostMapping("/compute")
    public TariffComputeResponse compute(
        @RequestParam Integer id,
        @RequestBody TariffComputeRequest req
    ) {
        return tariffService.computeTariff(id ,req);
    }

    // CREATE
    @PostMapping
    public Tariff createTariff(@RequestBody Tariff tariff) {
        return tariffService.createTariff(tariff);
    }

    // UPDATE
    @PutMapping("/{id}")
    public Tariff updateTariff(@PathVariable Integer id, @RequestBody Tariff tariff) {
        return tariffService.updateTariff(id, tariff);
    }

    // DELETE
    @DeleteMapping("/{id}")
    public void deleteTariff(@PathVariable Integer id) {
        tariffService.deleteTariff(id);
    }
}