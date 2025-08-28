package com.tariff.tariff_backend.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.model.Tariff;
import com.tariff.tariff_backend.model.dashboard.DashboardResponse;
import com.tariff.tariff_backend.repository.TariffRepo;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class DashboardService {

    @Autowired
    private final TariffRepo tariffRepo;

    public DashboardResponse createTariff(Tariff newTariff) {
        DashboardResponse response = new DashboardResponse(true, "Sucessfully created the new tariff.");
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
            response.setSuccess(false);
            response.setMessage("Internal server error. " + e.getMessage());
        }
        return response;
    }
}
