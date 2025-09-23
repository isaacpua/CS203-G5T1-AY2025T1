package com.tariff.tariff_backend.controller;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
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
        Page<TariffSearchRow> results = tariffService.searchTariffs(
            tariffid, descriptionwcountry, partnercountry, reportercountry,
            unitid, name, category, advalorem, specificperunit, id, pageable
        );

        // If DB returns no rows, provide 3 mocked rows for development/demo so the UI shows data
        if (results == null || results.isEmpty()) {
            List<TariffSearchRow> demo = new ArrayList<>();
            demo.add(new TariffSearchRow(
                1,
                12345,
                "Sunglasses, plastic frame - USA",
                "Sunglasses",
                "AD_VALOREM",
                false,
                840,
                840,
                1,
                "Apparel",
                new BigDecimal("0.10"),
                new BigDecimal("0.00"),
                new BigDecimal("0.10"),
                new BigDecimal("0.00")
            ));
            demo.add(new TariffSearchRow(
                2,
                23456,
                "LED bulbs, 5W - China",
                "LED Bulb",
                "SPECIFIC_PER_UNIT",
                false,
                156,
                156,
                2,
                "Electronics",
                new BigDecimal("0.00"),
                new BigDecimal("0.50"),
                new BigDecimal("0.00"),
                new BigDecimal("0.50")
            ));
            demo.add(new TariffSearchRow(
                3,
                34567,
                "Cotton T-shirt - India",
                "T-Shirt",
                "FREE",
                true,
                356,
                356,
                1,
                "Apparel",
                new BigDecimal("0.00"),
                new BigDecimal("0.00"),
                new BigDecimal("0.00"),
                new BigDecimal("0.00")
            ));

            return new PageImpl<>(demo, pageable, demo.size());
        }

        return results;
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