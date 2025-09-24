package com.tariff.tariff_backend.service;

import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.model.Tariff;
import com.tariff.tariff_backend.model.dashboard.DashboardMetrics;
import com.tariff.tariff_backend.model.dashboard.DashboardResponse;
import com.tariff.tariff_backend.model.dashboard.TariffPatchDTO;
import com.tariff.tariff_backend.repository.TariffRepo;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class DashboardService {

    @Autowired
    private final TariffRepo tariffRepo;

    public DashboardResponse createTariff(Tariff newTariff) {
        DashboardResponse response = new DashboardResponse(true, "Sucessfully created the new tariff.");
        Integer tariffid = newTariff.getTariffid();
        try {
            if (tariffRepo.existsById(tariffid)) {
                throw new Exception("Unable to create new tariff because the Tariff ID " + tariffid + " already exists.");
            }

            Tariff savedTariff = tariffRepo.save(newTariff);

            if (savedTariff == null || !tariffRepo.existsById(tariffid)) {
                throw new Exception("Unable to create the new tariff.");
            }
        } catch (Exception e) {
            response.setSuccess(false);
            response.setMessage(e.getMessage());
        }
        return response;
    }

    public DashboardResponse updateTariff(Integer tariffid, TariffPatchDTO patchDTO) {
        DashboardResponse response = new DashboardResponse(true, "Sucessfully updated the tariff.");
        try {
            Optional<Tariff> optionalTariff = tariffRepo.findById(tariffid);
            if (optionalTariff.isEmpty()) {
                throw new Exception("Tariff with ID " + tariffid + " not found");
            }
            Tariff existingTariff = optionalTariff.get();

            if (patchDTO.getTariffid() != null) {
                if (!patchDTO.getTariffid().equals(tariffid) && tariffRepo.existsById(patchDTO.getTariffid())) {
                    throw new Exception("Unable to update tariff because the new Tariff ID " + patchDTO.getTariffid() + " already exists.");
                }
                existingTariff.setTariffid(patchDTO.getTariffid());
            }

            if (patchDTO.getDescriptionwcountry() != null) {
                existingTariff.setDescriptionwcountry(patchDTO.getDescriptionwcountry());
            }

            tariffRepo.save(existingTariff);

        } catch (Exception e) {
            response.setSuccess(false);
            response.setMessage(e.getMessage());
        }
        return response;
    }

    public DashboardResponse deleteTariff(Integer tariffid) {
        DashboardResponse response = new DashboardResponse(true, "Sucessfully deleted the tariff.");
        try {
            if (!tariffRepo.existsById(tariffid)) {
                throw new Exception("Tariff with ID " + tariffid + " not found");
            }

            tariffRepo.deleteById(tariffid);

            if (tariffRepo.existsById(tariffid)) {
                throw new Exception("Failed to delete tariff with ID " + tariffid);
            }
        } catch (Exception e) {
            response.setSuccess(false);
            response.setMessage(e.getMessage());
        }
        return response;
    }

    public DashboardMetrics getTariffs(Integer tariffId, String descriptionQuery, Pageable pageable) {
        Page<Tariff> pageResult;

        if (tariffId != null) {
            pageResult = tariffRepo.findByTariffid(tariffId, pageable);
        } else if (descriptionQuery != null && !descriptionQuery.isBlank()) {
            pageResult = tariffRepo.findByDescriptionwcountryContainingIgnoreCase(descriptionQuery, pageable);
        } else {
            pageResult = tariffRepo.findAll(pageable);
        }

        return new DashboardMetrics(
                pageResult.getContent(),
                pageResult.getNumber(),
                pageResult.getTotalPages(),
                pageResult.getTotalElements());
    }
}