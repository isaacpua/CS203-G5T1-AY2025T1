package com.tariff.tariff_backend.service;

import java.util.List;
import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.dto.TariffPatchDTO;
import com.tariff.tariff_backend.model.dashboard.DashboardMetrics;
import com.tariff.tariff_backend.model.dashboard.DashboardResponse;
import com.tariff.tariff_backend.model.tariffs_new.Country;
import com.tariff.tariff_backend.model.tariffs_new.Tariff;
import com.tariff.tariff_backend.repository.CountryRepo;
import com.tariff.tariff_backend.repository.TariffRepo;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class DashboardService {

    @Autowired
    private final TariffRepo tariffRepo;
    @Autowired
    private final CountryRepo countryRepo;

    public DashboardResponse createTariff(TariffPatchDTO newTariffDTO) {
        DashboardResponse response = new DashboardResponse(true, "Sucessfully created the new tariff.");
        try {
            System.out.println("Building new Tariff WOWWWWWWWW");
            System.out.println(newTariffDTO);
            List<Country> partnerCountries = countryRepo.findByName(newTariffDTO.getPartnerCountry());
            if (partnerCountries.size() == 0) {
                throw new Exception("Country " + newTariffDTO.getPartnerCountry() + " not found in database");
            }
            List<Country> reporterCountries = countryRepo.findByName(newTariffDTO.getReporterCountry());
            if (reporterCountries.size() == 0) {
                throw new Exception("Country " + newTariffDTO.getReporterCountry() + " not found in database");
            }
            Tariff newTariff = Tariff.builder()
                    .tariffId(newTariffDTO.getTariffId())
                    .descriptionwcountry(newTariffDTO.getDescriptionwcountry())
                    .partnerCountry(partnerCountries.get(0))
                    .reporterCountry(reporterCountries.get(0))
                    .unitname(newTariffDTO.getUnitname())
                    .category(newTariffDTO.getCategory())
                    .adValorem(newTariffDTO.getAdValorem())
                    .specificPerUnit(newTariffDTO.getSpecificPerUnit())
                    .effectivedate(newTariffDTO.getEffectivedate())
                    .expirydate(newTariffDTO.getExpirydate())
                    .datasource(newTariffDTO.getDatasource())
                    .year(newTariffDTO.getYear())
                    .build();

            Tariff savedTariff = tariffRepo.save(newTariff);
            String tariffId = savedTariff.getTariffId();

            if (savedTariff == null || !tariffRepo.existsById(tariffId)) {
                throw new Exception("Unable to create the new tariff.");
            }
        } catch (Exception e) {
            response.setSuccess(false);
            response.setMessage(e.getMessage());
        }
        return response;
    }

    public DashboardResponse updateTariff(String tariffId, TariffPatchDTO patchDTO) {
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
                List<Country> partnerCountries = countryRepo.findByName(patchDTO.getPartnerCountry());
                if (partnerCountries.size() == 0) {
                    throw new Exception("Country " + patchDTO.getPartnerCountry() + " not found in database");
                }
                existingTariff.setPartnerCountry(partnerCountries.get(0));
            }
            if (patchDTO.getReporterCountry() != null) {
                List<Country> reporterCountries = countryRepo.findByName(patchDTO.getReporterCountry());
                if (reporterCountries.size() == 0) {
                    throw new Exception("Country " + patchDTO.getReporterCountry() + " not found in database");
                }
                existingTariff.setReporterCountry(reporterCountries.get(0));
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
            if (patchDTO.getYear() != null) {
                existingTariff.setYear(patchDTO.getYear());
            }
            existingTariff.setEffectivedate(patchDTO.getEffectivedate());
            existingTariff.setExpirydate(patchDTO.getExpirydate());
            if (patchDTO.getDatasource() != null) { // Datasource might be nullable in DB
                existingTariff.setDatasource(patchDTO.getDatasource());
            }

            tariffRepo.save(existingTariff);

        } catch (Exception e) {
            response.setSuccess(false);
            response.setMessage(e.getMessage());
        }
        return response;
    }

    public DashboardResponse deleteTariff(String tariffId) {
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

    public DashboardMetrics getTariffs(String tariffId, String descriptionQuery, Pageable pageable, Integer fromYear, Integer toYear) {
        Page<Tariff> pageResult;
        String query;
        if (descriptionQuery != null) { 
            query = descriptionQuery.trim();
        } else {
            query = descriptionQuery;
        }

        if (fromYear == null || toYear == null) {
            if (tariffId != null && !tariffId.isBlank()) {
                System.out.println("service: tariffid query is: " + tariffId);
                pageResult = tariffRepo.findByTariffIdContaining(tariffId, pageable);
            } else if (query != null && !query.isBlank()) {
                pageResult = tariffRepo.findByDescriptionwcountryContainingIgnoreCase(query, pageable);
            } else {
                pageResult = tariffRepo.findAll(pageable);
            }
        } else {
            if (tariffId != null && !tariffId.isBlank()) {
                pageResult = tariffRepo.findByYearBetweenAndTariffIdContaining(fromYear, toYear, tariffId, pageable);
            } else if (query != null && !query.isBlank()) {
                pageResult = tariffRepo.findByYearBetweenAndDescriptionwcountryContainingIgnoreCase(fromYear, toYear, query, pageable);
            } else {
                pageResult = tariffRepo.findByYearBetween(fromYear, toYear, pageable);
            }
        }

        List<TariffPatchDTO> tariffDtoList = pageResult.getContent().stream()
                .map(tariff -> new TariffPatchDTO(
                        tariff.getTariffId(),
                        tariff.getDescriptionwcountry(),
                        tariff.getPartnerCountry().getName(),
                        tariff.getReporterCountry().getName(),
                        tariff.getUnitname(),
                        tariff.getCategory(),
                        tariff.getAdValorem(),
                        tariff.getSpecificPerUnit(),
                        tariff.getEffectivedate(),
                        tariff.getExpirydate(),
                        tariff.getDatasource(),
                        tariff.getYear()))
                .toList();

        return new DashboardMetrics(
                tariffDtoList,
                pageResult.getNumber(),
                pageResult.getTotalPages(),
                pageResult.getTotalElements());
    }

    public List<TariffPatchDTO> getAllTariffs() {
        Sort sort = Sort.by(Sort.Direction.ASC, "tariffId");
        return tariffRepo.findAll(sort).stream()
                .map(tariff -> new TariffPatchDTO(
                        tariff.getTariffId(),
                        tariff.getDescriptionwcountry(),
                        tariff.getPartnerCountry().getName(),
                        tariff.getReporterCountry().getName(),
                        tariff.getUnitname(),
                        tariff.getCategory(),
                        tariff.getAdValorem(),
                        tariff.getSpecificPerUnit(),
                        tariff.getEffectivedate(),
                        tariff.getExpirydate(),
                        tariff.getDatasource(),
                        tariff.getYear()))
                .toList();
    }
}
