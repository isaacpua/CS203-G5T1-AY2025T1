package com.tariff.tariff_backend.service;

import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.model.tariffs_new.Tariff;
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

    public DashboardResponse createTariff(TariffPatchDTO newTariffDTO) {
        DashboardResponse response = new DashboardResponse(true, "Sucessfully created the new tariff.");
        try {
            System.out.println("Building new Tariff WOWWWWWWWW");
             Tariff newTariff = Tariff.builder()
                .descriptionwcountry(newTariffDTO.getDescriptionwcountry())
                .partnerCountry(newTariffDTO.getPartnerCountry())
                .reporterCountry(newTariffDTO.getReporterCountry())
                .unitname(newTariffDTO.getUnitname())
                .category(newTariffDTO.getCategory())
                .adValorem(newTariffDTO.getAdValorem())
                .specificPerUnit(newTariffDTO.getSpecificPerUnit())
                .build();

            Tariff savedTariff = tariffRepo.save(newTariff);
            Integer tariffId = savedTariff.getTariffId();

            if (savedTariff == null || !tariffRepo.existsById(tariffId)) {
                throw new Exception("Unable to create the new tariff.");
            }
        } catch (Exception e) {
            response.setSuccess(false);
            response.setMessage(e.getMessage());
        }
        return response;
    }

    public DashboardResponse updateTariff(Integer tariffId, TariffPatchDTO patchDTO) {
        DashboardResponse response = new DashboardResponse(true, "Sucessfully updated the tariff.");
        try {
            Optional<Tariff> optionalTariff = tariffRepo.findById(tariffId);
            if (optionalTariff.isEmpty()) {
                throw new Exception("Tariff with ID " + tariffId + " not found");
            }
            Tariff existingTariff = optionalTariff.get();

            if (patchDTO.getDescriptionwcountry() != null) {
                existingTariff.setDescriptionwcountry(patchDTO.getDescriptionwcountry());
            }
            
            // Add the rest of the fields
            if (patchDTO.getPartnerCountry() != null) {
                existingTariff.setPartnerCountry(patchDTO.getPartnerCountry());
            }
            if (patchDTO.getReporterCountry() != null) {
                existingTariff.setReporterCountry(patchDTO.getReporterCountry());
            }
            if (patchDTO.getUnitname() != null) {
                existingTariff.setUnitname(patchDTO.getUnitname());
            }
            if (patchDTO.getCategory() != null) {
                existingTariff.setCategory(patchDTO.getCategory());
            }
            if (patchDTO.getAdValorem() != null) {
                existingTariff.setAdValorem(patchDTO.getAdValorem());
            }
            if (patchDTO.getSpecificPerUnit() != null) {
                existingTariff.setSpecificPerUnit(patchDTO.getSpecificPerUnit());
            }


            tariffRepo.save(existingTariff);

        } catch (Exception e) {
            response.setSuccess(false);
            response.setMessage(e.getMessage());
        }
        return response;
    }

    public DashboardResponse deleteTariff(Integer tariffId) {
        DashboardResponse response = new DashboardResponse(true, "Sucessfully deleted the tariff.");
        try {
            if (!tariffRepo.existsById(tariffId)) {
                throw new Exception("Tariff with ID " + tariffId + " not found");
            }

            tariffRepo.deleteById(tariffId);

            if (tariffRepo.existsById(tariffId)) {
                throw new Exception("Failed to delete tariff with ID " + tariffId);
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
            pageResult = tariffRepo.findByTariffId(tariffId, pageable);
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