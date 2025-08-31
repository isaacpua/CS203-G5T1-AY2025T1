package com.tariff.tariff_backend.service;

import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.model.Tariff;
import com.tariff.tariff_backend.model.TariffSearchRow;
import com.tariff.tariff_backend.repository.TariffRepo;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor // auto generates constructors 
public class TariffService {
    private final TariffRepo tariffRepo;

     public Page<TariffSearchRow> searchTariffs(Integer id, Integer hts8, String q, Pageable pageable) {
        Page<Tariff> page;

        if (id != null) {
            var one = tariffRepo.findById(id);
            if (one.isEmpty()) return Page.empty(pageable);
            return new PageImpl<>(List.of(one.get()), pageable, 1).map(this::toRow);
        }

        if (hts8 != null) {
            page = tariffRepo.findByHts8(hts8, pageable);
            return page.map(this::toRow);
        }

        if (q != null && !q.isBlank()) {
            page = tariffRepo.findByBriefDescriptionContainingIgnoreCase(q.trim(), pageable);
            return page.map(this::toRow);
        }

        // no criteria → empty page (or define default browse)
        return Page.empty(pageable);
    }

    private TariffSearchRow toRow(Tariff t) {
        // Optional: add lightweight parser metadata for the list
        String overallKind = null;
        boolean isFree = false;
        try {
            var parsed = RateParser.parse(t.getMfnTextRate());
            overallKind = parsed.overallKind().name();
            isFree = parsed.isFree();
        } catch (Exception ignore) {}

        return new TariffSearchRow(
            t.getId(),
            t.getHts8(),
            t.getBriefDescription(),
            t.getMfnTextRate(),
            overallKind,
            isFree
        );
    }
}