package com.tariff.tariff_backend.service;

import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.model.dashboard.DashboardResponse;
import com.tariff.tariff_backend.model.dashboard.TariffPatchDTO;
import com.tariff.tariff_backend.model.tariffs_old.Tariff;
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
                throw new Exception("Unable to create new tariff because the HTS8 code " + hts8 + " already exists.");
            }

            Tariff savedTariff = tariffRepo.save(newTariff);

            if (savedTariff == null || tariffRepo.findByHts8(hts8).isEmpty()) {
                throw new Exception("Unable to create the new tariff.");
            }
        } catch (Exception e) {
            response.setSuccess(false);
            response.setMessage(e.getMessage());
        }
        return response;
    }

    public DashboardResponse updateTariff(Integer id, TariffPatchDTO patchDTO) {
        DashboardResponse response = new DashboardResponse(true, "Sucessfully updated the tariff.");
        Integer hts8 = patchDTO.getHts8();
        String briefDescription = patchDTO.getBriefDescription();
        String mfnTextRate = patchDTO.getMfnTextRate();
        try {
            Optional<Tariff> optionalTariff = tariffRepo.findById(id);
            if (optionalTariff.isEmpty()) {
                throw new Exception("Tariff with ID " + id + " not found");
            }
            Tariff existingTariff = optionalTariff.get();

            if (hts8 != null) {
                if (!tariffRepo.findByHts8(hts8).isEmpty()) {
                    throw new Exception("Unable to update tariff because the HTS8 code " + hts8 + " already exists.");
                }
                existingTariff.setHts8(hts8);
            }

            if (briefDescription != null) {
                existingTariff.setBriefDescription(briefDescription);
            }

            if (mfnTextRate != null) {
                existingTariff.setMfnTextRate(mfnTextRate);
            }

            Tariff updatedTariff = tariffRepo.save(existingTariff);
            if (hts8 != null && !updatedTariff.getHts8().equals(hts8)) {
                throw new Exception("Failed to update the HTS8 code.");
            }
            if (briefDescription != null && !updatedTariff.getBriefDescription().equals(briefDescription)) {
                throw new Exception("Failed to update the brief_description.");
            }
            if (mfnTextRate != null && !updatedTariff.getMfnTextRate().equals(mfnTextRate)) {
                throw new Exception("Failed to update the mfn_text_rate.");
            }
        } catch (Exception e) {
            response.setSuccess(false);
            response.setMessage(e.getMessage());
        }
        return response;
    }

    public DashboardResponse deleteTariff(Integer id) {
        DashboardResponse response = new DashboardResponse(true, "Sucessfully deleted the tariff.");
        try {
            if (tariffRepo.findById(id).isEmpty()) {
                throw new Exception("Tariff with ID " + id + " not found");
            }

            tariffRepo.deleteById(id);

            if (!tariffRepo.findById(id).isEmpty()) {
                throw new Exception("Failed to delete tariff with ID " + id);
            }
        } catch (Exception e) {
            response.setSuccess(false);
            response.setMessage(e.getMessage());
        }
        return response;
    }
}
