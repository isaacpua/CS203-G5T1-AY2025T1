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
            if (!tariffRepo.findByTariffid(tariffid).isEmpty()) {
                throw new Exception("Unable to create new tariff because the Tariff ID " + tariffid + " already exists.");
            }

            Tariff savedTariff = tariffRepo.save(newTariff);

            if (savedTariff == null || tariffRepo.findByTariffid(tariffid).isEmpty()) {
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
            Integer tariffid = patchDTO.getTariffid();
            String descriptionwcountry = patchDTO.getDescriptionwcountry();
            String name = patchDTO.getName();
        try {
            Optional<Tariff> optionalTariff = tariffRepo.findById(id);
            if (optionalTariff.isEmpty()) {
                throw new Exception("Tariff with ID " + id + " not found");
            }
            Tariff existingTariff = optionalTariff.get();

                if (tariffid != null) {
                    if (!tariffRepo.findByTariffid(tariffid).isEmpty()) {
                        throw new Exception("Unable to update tariff because the Tariff ID " + tariffid + " already exists.");
                }
                    existingTariff.setTariffid(tariffid);
            }

                if (descriptionwcountry != null) {
                    existingTariff.setDescriptionwcountry(descriptionwcountry);
            }

                if (name != null) {
                    existingTariff.setName(name);
            }

            Tariff updatedTariff = tariffRepo.save(existingTariff);
                if (tariffid != null && !updatedTariff.getTariffid().equals(tariffid)) {
                    throw new Exception("Failed to update the Tariff ID.");
            }
                if (descriptionwcountry != null && !updatedTariff.getDescriptionwcountry().equals(descriptionwcountry)) {
                    throw new Exception("Failed to update the descriptionwcountry.");
            }
                if (name != null && !updatedTariff.getName().equals(name)) {
                    throw new Exception("Failed to update the name.");
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
