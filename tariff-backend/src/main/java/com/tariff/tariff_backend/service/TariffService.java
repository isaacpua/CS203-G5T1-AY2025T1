package com.tariff.tariff_backend.service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.model.tariffs_old.Tariff;
import com.tariff.tariff_backend.model.tariffs_old.TariffComputeRequest;
import com.tariff.tariff_backend.model.tariffs_old.TariffComputeResponse;
import com.tariff.tariff_backend.model.tariffs_old.TariffSearchRow;
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

        if (id != null) { // Id lookup
            Optional<Tariff> one = tariffRepo.findById(id);
            if (one.isPresent()) {
                List<Tariff> resultList = new ArrayList<>();
                resultList.add(one.get());

                page = new PageImpl<>(resultList, pageable, 1); // creating page manually
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

        // If no criteria, return all tariffs (default browse mode)
        page = tariffRepo.findAll(pageable);
        return page.map(this::toRow);
    }

    private TariffSearchRow toRow(Tariff t) {
        String overallKind = null;
        boolean isFree = false;
        try {
            var parsed = RateParser.parse(t.getMfnTextRate());
            overallKind = parsed.overallKind().name();
            isFree = parsed.isFree();
        } catch (Exception ignore) {
        }

        return new TariffSearchRow(
                t.getId(),
                t.getHts8(),
                t.getBriefDescription(),
                t.getMfnTextRate(),
                overallKind,
                isFree);
    }

    public TariffComputeResponse computeTariff(Integer id, TariffComputeRequest req) {
        Tariff t = tariffRepo.findById(id).orElseThrow(() -> new IllegalArgumentException("Tariff not found: " + id));
        ParsedRate parsed = RateParser.parse(t.getMfnTextRate());

        BigDecimal declared;
        BigDecimal qty;

        if (req.declaredValue() == null) {
            declared = BigDecimal.ZERO;
        } else {
            declared = req.declaredValue();
        }

        if (req.quantity() == null) {
            qty = BigDecimal.ZERO;
        } else {
            qty = req.quantity();
        }
        String uom = req.uom();
        TariffComputeResponse cascade = tryComputeCascadeNoMap(parsed, declared, qty, uom);
        if (cascade != null) {
            return cascade;
        }
        BigDecimal totalDuty = BigDecimal.ZERO;

        List<TariffComputeResponse.BreakdownLine> lines = new ArrayList<>();

        List<RateParser.RateComponent> comps = parsed.components();

        for (RateParser.RateComponent c : comps) {

            if (c.kind() == RateParser.RateKind.FREE || c.kind() == RateParser.RateKind.UNKNOWN) {
                continue;
            }

            if (c.kind() == RateParser.RateKind.AD_VALOREM) {
                // c.adValorem is already a fraction
                BigDecimal base = declared;
                if (c.qualifier() != null && req.declaredByQualifier() != null) {
                    BigDecimal override = req.declaredByQualifier().get(c.qualifier());
                    if (override != null) {
                        base = override;
                    }
                }
                BigDecimal duty = base.multiply(c.adValorem());
                totalDuty = totalDuty.add(duty);
                lines.add(new TariffComputeResponse.BreakdownLine(RateKind.AD_VALOREM, duty, c.adValorem(), null, null,
                        c.qualifier()));
                continue;
            }

            if (c.kind() == RateParser.RateKind.SPECIFIC_PER_UNIT) {
                BigDecimal rate = c.specificPerUnit();
                BigDecimal duty = rate.multiply(qty);

                totalDuty = totalDuty.add(duty);
                lines.add(new TariffComputeResponse.BreakdownLine(RateKind.SPECIFIC_PER_UNIT, duty, null, rate,
                        c.unit(), c.qualifier()));
            }
        }
        return new TariffComputeResponse(totalDuty, declared, lines);
    }

    private TariffComputeResponse tryComputeCascadeNoMap(
            ParsedRate parsed,
            BigDecimal declared,
            BigDecimal qty,
            String uom) {
        RateParser.RateComponent adComp = null; // unqualified %
        List<RateParser.RateComponent> specificComps = new ArrayList<>();

        for (RateParser.RateComponent c : parsed.components()) {
            if (c.kind() == RateParser.RateKind.AD_VALOREM &&
                    (c.qualifier() == null || c.qualifier().isBlank())) {
                if (adComp == null) {
                    adComp = c; // first unqualified %
                } else {
                    // more than one unqualified % → not a simple cascade
                    return null;
                }
            }
            if (c.kind() == RateParser.RateKind.SPECIFIC_PER_UNIT) {
                specificComps.add(c);
            }
        }

        if (adComp == null || specificComps.isEmpty()) {
            return null; // not a cascade case
        }

        // Compute specifics
        BigDecimal specSubtotal = BigDecimal.ZERO;
        List<TariffComputeResponse.BreakdownLine> lines = new ArrayList<>();

        // Normalize uom
        String normUom = (uom == null) ? null : uom.trim().toLowerCase();

        // Track if we matched at least one unit with uom
        boolean anyMatchedUom = false;

        for (RateParser.RateComponent sc : specificComps) {
            String unit = (sc.unit() == null || sc.unit().isBlank())
                    ? "each"
                    : sc.unit().trim().toLowerCase();

            // Decide which quantity to use for this specific line
            BigDecimal qForUnit = BigDecimal.ZERO;

            // match by explicit uom
            if (normUom != null && !normUom.isBlank()) {
                if (unit.equals(normUom)) {
                    qForUnit = qty;
                    anyMatchedUom = true;
                }
            } else {
                // if uom not provided, "each" is a sensible default
                if ("each".equals(unit)) {
                    qForUnit = qty;
                    anyMatchedUom = true;
                }
            }

            BigDecimal rate = sc.specificPerUnit(); // already per one unit via parser normalization
            BigDecimal specDuty = rate.multiply(qForUnit == null ? BigDecimal.ZERO : qForUnit);

            lines.add(new TariffComputeResponse.BreakdownLine(
                    RateKind.SPECIFIC_PER_UNIT,
                    specDuty,
                    null,
                    rate,
                    unit,
                    sc.qualifier()));

            specSubtotal = specSubtotal.add(specDuty);
        }

        // If nothing matched uom (e.g., multiple units present, one quantity provided),
        // fallback: apply the same qty to ALL specific lines (temporary behavior).
        if (!anyMatchedUom && qty != null && qty.compareTo(BigDecimal.ZERO) > 0) {
            specSubtotal = BigDecimal.ZERO;
            lines.clear();
            for (RateParser.RateComponent sc : specificComps) {
                String unit = (sc.unit() == null || sc.unit().isBlank())
                        ? "each"
                        : sc.unit().trim().toLowerCase();
                BigDecimal rate = sc.specificPerUnit();
                BigDecimal specDuty = rate.multiply(qty);
                lines.add(new TariffComputeResponse.BreakdownLine(
                        RateKind.SPECIFIC_PER_UNIT,
                        specDuty,
                        null,
                        rate,
                        unit,
                        sc.qualifier()));
                specSubtotal = specSubtotal.add(specDuty);
            }
        }

        // Apply the unqualified % onto the subtotal
        BigDecimal adVal = (adComp.adValorem() == null) ? BigDecimal.ZERO : adComp.adValorem();
        BigDecimal adDuty = specSubtotal.multiply(adVal);

        lines.add(new TariffComputeResponse.BreakdownLine(
                RateKind.AD_VALOREM,
                adDuty,
                adVal,
                null,
                null,
                "(applied on specific duty subtotal)"));

        BigDecimal totalDuty = specSubtotal.add(adDuty);
        return new TariffComputeResponse(totalDuty, declared, lines);
    }
}