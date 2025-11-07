package com.tariff.tariff_backend.service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.model.tariffs_new.Country;
import com.tariff.tariff_backend.model.tariffs_new.Tariff;
import com.tariff.tariff_backend.model.tariffs_new.TariffSearchRow;
import com.tariff.tariff_backend.repository.TariffRepo;


import jakarta.persistence.criteria.Predicate;
import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor // auto generates constructors
public class TariffService {
    // CREATE
    private final TariffRepo tariffRepo;

    public Page<TariffSearchRow> searchTariffs(
        Integer tariffId,
        String descriptionwcountry,
        Country partnerCountry,
        Country reporterCountry,
        String unitname,
        String category,
        BigDecimal adValorem,
        BigDecimal specificPerUnit,
        Pageable pageable
    ) {
        // Use JPA Specification for flexible filtering
        return tariffRepo.findAll((root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            if (tariffId != null) predicates.add(cb.equal(root.get("tariffId"), tariffId));
            if (descriptionwcountry != null && !descriptionwcountry.isBlank()) predicates.add(cb.like(cb.lower(root.get("descriptionwcountry")), "%" + descriptionwcountry.toLowerCase() + "%"));
            if (partnerCountry != null) predicates.add(cb.equal(root.get("partnerCountry"), partnerCountry));
            if (reporterCountry != null) predicates.add(cb.equal(root.get("reporterCountry"), reporterCountry));
            if (unitname != null && !unitname.isBlank()) predicates.add(cb.like(cb.lower(root.get("unitname")), "%" + unitname.toLowerCase() + "%"));
            if (category != null && !category.isBlank()) predicates.add(cb.like(cb.lower(root.get("category")), "%" + category.toLowerCase() + "%"));
            if (adValorem != null) predicates.add(cb.equal(root.get("adValorem"), adValorem));
            if (specificPerUnit != null) predicates.add(cb.equal(root.get("specificPerUnit"), specificPerUnit));
            return cb.and(predicates.toArray(new Predicate[0]));
        }, pageable).map(this::toRow);
    }

    private TariffSearchRow toRow(Tariff t) {
        // Map new fields to TariffSearchRow (update constructor as needed)
        return new TariffSearchRow(
            t.getTariffId(),
            t.getDescriptionwcountry(),
            t.getPartnerCountry(),
            t.getReporterCountry(),
            t.getUnitname(),
            t.getCategory(),
            t.getAdValorem(),
            t.getSpecificPerUnit());
    }



    // CREATE
    public Tariff createTariff(Tariff tariff) {
        return tariffRepo.save(tariff);
    }

    // UPDATE
    public Tariff updateTariff(String tariffId, Tariff patch) {
    Tariff existing = tariffRepo.findById(tariffId).orElseThrow(() -> new IllegalArgumentException("Tariff not found: " + tariffId));
    // Update fields
    existing.setTariffId(patch.getTariffId());
    existing.setCategory(patch.getCategory());
    existing.setDescriptionwcountry(patch.getDescriptionwcountry());
    existing.setPartnerCountry(patch.getPartnerCountry());
    existing.setReporterCountry(patch.getReporterCountry());
    existing.setAdValorem(patch.getAdValorem());
    existing.setSpecificPerUnit(patch.getSpecificPerUnit());
    existing.setUnitname(patch.getUnitname());
    return tariffRepo.save(existing);
    }

    // DELETE
    public void deleteTariff(String tariffId) {
        tariffRepo.deleteById(tariffId);
    }
}
