package com.tariff.tariff_backend.service;

import java.math.BigDecimal;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.NoSuchElementException;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.dto.CalculationDTO.CalculateDutyRequest;
import com.tariff.tariff_backend.dto.CalculationDTO.CalculateDutyResponse;
import com.tariff.tariff_backend.model.User;
import com.tariff.tariff_backend.model.tariffs_new.Tariff;
import com.tariff.tariff_backend.model.tariffs_new.TransactionLine;
import com.tariff.tariff_backend.repository.TariffRepo;
import com.tariff.tariff_backend.repository.TransactionLineRepo;
import com.tariff.tariff_backend.repository.UserRepo;

@Service

public class CalculationService {

    private final TariffRepo tariffRepo;
    private final TransactionLineRepo txRepo;
    private final UserRepo userRepo;

    public CalculationService(TariffRepo tariffRepo, TransactionLineRepo txRepo, UserRepo userRepo) {
        this.tariffRepo = tariffRepo;
        this.txRepo = txRepo;
        this.userRepo = userRepo;
    }

    public CalculateDutyResponse calculateAndStore(CalculateDutyRequest request) {
        if (request.tariffId() == null) {
            throw new IllegalArgumentException("tariffID is needed");
        }
        if (request.customsValue() == null && request.quantity() == null) {
            throw new IllegalArgumentException("Provide a Value and/or quantity");
        }

        Tariff tariff = null; // getting tariffs
        try {
            tariff = tariffRepo.findById(request.tariffId()).get();
        } catch (NoSuchElementException e) {
            throw new IllegalArgumentException("Tariff not found: " + request.tariffId());
        }

        Authentication auth = SecurityContextHolder.getContext().getAuthentication(); // getting username because my frontend not sending
        String username = null;
        if (auth != null) {
            username = auth.getName();
        }
        if (username == null) {
            throw new IllegalArgumentException("No authenticated user");
        }

        User user = null; // getting user
        try {
            user = userRepo.findByUsername(username).get();
        } catch (NoSuchElementException e) {
            throw new IllegalArgumentException("User not found: " + username);
        }

        BigDecimal advalorem = tariff.getAdValorem(); // our db is 0.05 for 5% so becomes 1.05
        if (advalorem != null) {
            advalorem = advalorem.add(BigDecimal.ONE);
        }
        BigDecimal specificPerUnit = tariff.getSpecificPerUnit();
        String category = tariff.getCategory().toLowerCase();
        BigDecimal inputValue = request.customsValue();
        BigDecimal quantity = request.quantity();

        BigDecimal price = null;
        if (category.equals("ad_valorem")) {
            if (inputValue == null) {
                throw new IllegalArgumentException("Please input a value");
            }
            price = inputValue.multiply(advalorem);
        }
        if (category.equals("specific_per_unit")) {
            if (quantity == null) {
                throw new IllegalArgumentException("Please input a quantity");
            }
            if (!isWholeNumber(quantity)) {
                throw new IllegalArgumentException("Please put a whole number");
            }
            price = quantity.multiply(specificPerUnit);
        }
        if (category.equals("composite")) {
            if (quantity == null) {
                throw new IllegalArgumentException("Please input a quantity");
            }
            if (!isWholeNumber(quantity)) {
                throw new IllegalArgumentException("Please put a whole number");
            }
            BigDecimal specPart = quantity.multiply(specificPerUnit);
            price = specPart.multiply(advalorem);
        }

        if (price == null) {
            throw new IllegalArgumentException("price not calculated");
        }
        if (request.save() == true) {
            TransactionLine tx = new TransactionLine();
            tx.setUser(user);
            try {
                Map<String, Object> snap = new LinkedHashMap<>();
                snap.put("tariffId", tariff.getTariffId());
                snap.put("descriptionwcountry", tariff.getDescriptionwcountry());
                snap.put("partnerCountry", tariff.getPartnerCountry().getName());
                snap.put("reporterCountry", tariff.getReporterCountry().getName());
                snap.put("unitname", tariff.getUnitname());
                snap.put("category", tariff.getCategory());
                snap.put("adValorem", tariff.getAdValorem());
                snap.put("specificPerUnit", tariff.getSpecificPerUnit());
                snap.put("quantity", request.quantity());
                snap.put("customsValue", request.customsValue());
                snap.put("total", price);
                tx.setSnapshot(snap);

            } catch (Exception e){
                System.err.println("Failed to serialize JSON: " + e.getMessage());
            }
            tx = txRepo.save(tx);
            return new CalculateDutyResponse(tx.getTransactionId(), tariff.getTariffId(), price); 
        } 
        return new CalculateDutyResponse(null, tariff.getTariffId(), price); 

    }

    private static boolean isWholeNumber(BigDecimal n) {
        if (n == null)
            return false;
        return n.stripTrailingZeros().scale() <= 0;
    }
}
