package com.tariff.tariff_backend.service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.model.Tariff;
import com.tariff.tariff_backend.model.TariffComputeRequest;
import com.tariff.tariff_backend.model.TariffComputeResponse;
import com.tariff.tariff_backend.model.TariffSearchRow;
import com.tariff.tariff_backend.repository.TariffRepo;
import com.tariff.tariff_backend.service.RateParser.ParsedRate;
import com.tariff.tariff_backend.service.RateParser.RateKind;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor // auto generates constructors 
public class TariffService {
    private final TariffRepo tariffRepo;

     public Page<TariffSearchRow> searchTariffs(Integer id, Integer hts8, String q, Pageable pageable) {
        Page<Tariff> page;

        if (id != null) { //Id lookup
            Optional<Tariff> one = tariffRepo.findById(id);
            if (one.isPresent()) {
                List<Tariff> resultList = new ArrayList<>();
                resultList.add(one.get());

                page = new PageImpl<>(resultList, pageable, 1); //creating page manually
                return page.map(this::toRow); // map is a helper to convert the page to rows based on my helper function
            } else {
                return Page.empty(pageable);
            }
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

    public TariffComputeResponse computeTariff(Integer id, TariffComputeRequest req){
        Tariff t = tariffRepo.findById(id).orElseThrow(() -> new IllegalArgumentException("Tariff not found: " + id));
        ParsedRate parsed = RateParser.parse(t.getMfnTextRate());
        
        BigDecimal declared;
        BigDecimal qty;

        if (req.declaredValue() == null) {
            declared = BigDecimal.ZERO;
        } else {
            declared = req.declaredValue();
        }

        if (req.quantity() == null){
            qty = BigDecimal.ZERO;
        } else {
            qty = req.quantity();
        }

        BigDecimal totalDuty = BigDecimal.ZERO;

        List<TariffComputeResponse.BreakdownLine> lines = new ArrayList<>();


        List<RateParser.RateComponent> comps = parsed.components();

        for (RateParser.RateComponent c : comps){

            if (c.kind() == RateParser.RateKind.FREE || c.kind() == RateParser.RateKind.UNKNOWN){
                continue;
            }
            if (c.kind() == RateParser.RateKind.AD_VALOREM) {
                //c.adValorem is already a fraction
                BigDecimal duty = c.adValorem();
                duty = duty.multiply(declared);
                totalDuty = totalDuty.add(duty);
                lines.add(new TariffComputeResponse.BreakdownLine(
                    RateKind.AD_VALOREM,
                    duty,
                    c.adValorem(),
                    null,
                    null,
                    c.qualifier()
                ));
                continue;
            }
            if (c.kind() == RateParser.RateKind.SPECIFIC_PER_UNIT){
                BigDecimal rate = c.specificPerUnit(); //for now doesnt work with those that have like 10 cents/1000
                BigDecimal duty = rate.multiply(qty);

                totalDuty = totalDuty.add(duty);
                lines.add(new TariffComputeResponse.BreakdownLine(
                    RateKind.SPECIFIC_PER_UNIT,
                    duty,
                    null,
                    rate,
                    c.unit(),
                    c.qualifier()
                ));
            }
        }
        return new TariffComputeResponse(
            totalDuty,
            declared,
            lines
        );
    }


}