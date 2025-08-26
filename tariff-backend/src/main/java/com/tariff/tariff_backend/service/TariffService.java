package com.tariff.tariff_backend.service;

import java.math.BigDecimal;
import java.math.RoundingMode;

import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.model.TariffRequest;
import com.tariff.tariff_backend.model.TariffResponse;

@Service
public class TariffService {

    public TariffResponse calculateTariff(TariffRequest request) {

        BigDecimal tariffRate;

        // Simple mock logic: determine the tariff rate based on product category
        // Use dictionary
        switch (request.getProductCategory().toLowerCase()) {
            case "electronics":
                tariffRate = new BigDecimal("0.15"); // 15%
                break;
            case "automotive":
                tariffRate = new BigDecimal("0.25"); // 25%
                break;
            default:
                tariffRate = new BigDecimal("0.05"); // 5% for all others
                break;
        }

        // Perform the calculation using BigDecimal for accuracy
        BigDecimal value = request.getValue();
        BigDecimal calculatedTariff = value.multiply(tariffRate).setScale(2, RoundingMode.HALF_UP);
        BigDecimal totalValue = value.add(calculatedTariff);

        return new TariffResponse(calculatedTariff, totalValue);
    }
}