package com.tariff.tariff_backend.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.model.Tariff;
import com.tariff.tariff_backend.model.dashboard.CreateResponse;
import com.tariff.tariff_backend.repository.TariffRepo;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class DashboardService {

    @Autowired
    private final TariffRepo tariffRepo;

    public CreateResponse createTariff(Tariff newTariff) {
        boolean success = true;
        String responseMsg = "Sucessfully created the new tariff.";
        Integer hts8 = newTariff.getHts8();
        try {
            if (!tariffRepo.findByHts8(hts8).isEmpty()) {
                throw new Exception("Unable to create new tariff because the hts8 code provided already exists in the database.");
            }

            Tariff savedTariff = tariffRepo.save(newTariff);

            if (savedTariff == null || tariffRepo.findByHts8(hts8).isEmpty()) {
                throw new Exception("Unable to create the new tariff.");
            }
        } catch (Exception e) {
            success = false;
            responseMsg = "Internal server error. " + e.getMessage();
            return new CreateResponse(success, responseMsg);
        }
        return new CreateResponse(success, responseMsg);
    }
}
