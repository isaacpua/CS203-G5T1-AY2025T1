package com.tariff.tariff_backend.service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.model.Tariff;
import com.tariff.tariff_backend.model.TariffComputeRequest;
import com.tariff.tariff_backend.model.TariffComputeResponse;
import com.tariff.tariff_backend.model.TariffSearchRow;
import com.tariff.tariff_backend.repository.TariffRepo;
import com.tariff.tariff_backend.service.RateParser.ParsedRate;
import com.tariff.tariff_backend.service.RateParser.RateKind;

import jakarta.persistence.criteria.Predicate;
import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor // auto generates constructors
public class TariffService {
    // CREATE
    private final TariffRepo tariffRepo;

    public Page<TariffSearchRow> searchTariffs(
        Integer tariffid,
        String descriptionwcountry,
        Integer partnercountry,
        Integer reportercountry,
        String unitname, // Changed from unitid
        String name,
        String category,
        Double advalorem,
        Double specificperunit,
        Integer id,
        Pageable pageable
    ) {
        // Use JPA Specification for flexible filtering
        return tariffRepo.findAll((root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            if (tariffid != null) predicates.add(cb.equal(root.get("tariffid"), tariffid));
            if (descriptionwcountry != null && !descriptionwcountry.isBlank()) predicates.add(cb.like(cb.lower(root.get("descriptionwcountry")), "%" + descriptionwcountry.toLowerCase() + "%"));
            if (partnercountry != null) predicates.add(cb.equal(root.get("partnercountry"), partnercountry));
            if (reportercountry != null) predicates.add(cb.equal(root.get("reportercountry"), reportercountry));
            // Updated to search by unitname
            if (unitname != null && !unitname.isBlank()) predicates.add(cb.like(cb.lower(root.get("unitname")), "%" + unitname.toLowerCase() + "%"));
            if (name != null && !name.isBlank()) predicates.add(cb.like(cb.lower(root.get("name")), "%" + name.toLowerCase() + "%"));
            if (category != null && !category.isBlank()) predicates.add(cb.like(cb.lower(root.get("category")), "%" + category.toLowerCase() + "%"));
            if (advalorem != null) predicates.add(cb.equal(root.get("advalorem"), advalorem));
            if (specificperunit != null) predicates.add(cb.equal(root.get("specificperunit"), specificperunit));
            if (id != null) predicates.add(cb.equal(root.get("id"), id));
            return cb.and(predicates.toArray(new Predicate[0]));
        }, pageable).map(this::toRow);
    }

    private TariffSearchRow toRow(Tariff t) {
        String overallKind = null;
        boolean isFree = false;
        try {
            var parsed = RateParser.parse(t.getDescriptionwcountry());
            overallKind = parsed.overallKind().name();
            isFree = parsed.isFree();
        } catch (Exception ignore) {
        }

        // Map new fields to TariffSearchRow (update constructor as needed)
        return new TariffSearchRow(
            t.getId(),
            t.getTariffid(),
            t.getDescriptionwcountry(),
            t.getName(),
            overallKind,
            isFree,
            t.getPartnercountry(),
            t.getReportercountry(),
            t.getUnitname(),
            t.getCategory(),
            t.getAdvalorem(),
            t.getSpecificperunit(),
            t.getAd_valorem(),
            t.getSpecific_per_unit());
    }

    public TariffComputeResponse computeTariff(Integer id, TariffComputeRequest req) {
        Tariff t = tariffRepo.findById(id).orElseThrow(() -> new IllegalArgumentException("Tariff not found: " + id));
        ParsedRate parsed = RateParser.parse(t.getDescriptionwcountry());

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

    // CREATE
    public Tariff createTariff(Tariff tariff) {
        return tariffRepo.save(tariff);
    }

    // UPDATE
    public Tariff updateTariff(Integer id, Tariff patch) {
        Tariff existing = tariffRepo.findById(id).orElseThrow(() -> new IllegalArgumentException("Tariff not found: " + id));
        // Update fields
        existing.setTariffid(patch.getTariffid());
        existing.setName(patch.getName());
        existing.setCategory(patch.getCategory());
        existing.setDescriptionwcountry(patch.getDescriptionwcountry());
        existing.setPartnercountry(patch.getPartnercountry());
        existing.setReportercountry(patch.getReportercountry());
        existing.setAdvalorem(patch.getAdvalorem());
        existing.setSpecificperunit(patch.getSpecificperunit());
        existing.setUnitname(patch.getUnitname());
        existing.setAd_valorem(patch.getAd_valorem());
        existing.setSpecific_per_unit(patch.getSpecific_per_unit());
        return tariffRepo.save(existing);
    }

    // DELETE
    public void deleteTariff(Integer id) {
        tariffRepo.deleteById(id);
    }
}