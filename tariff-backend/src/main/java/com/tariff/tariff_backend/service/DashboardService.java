package com.tariff.tariff_backend.service;

import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.tariff.tariff_backend.model.dashboard.DashboardResponse;
import com.tariff.tariff_backend.model.dashboard.TariffPatchDTO;
import com.tariff.tariff_backend.model.tariffs_new.Tariff;
import com.tariff.tariff_backend.repository.TariffRepo;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class DashboardService {

    @Autowired
    private final TariffRepo tariffRepo;

    public DashboardResponse createTariff(Tariff newTariff) {
        return null;
    }

    public DashboardResponse updateTariff(Integer id, TariffPatchDTO patchDTO) {
       return null;
    }

    public DashboardResponse deleteTariff(Integer id) {
       return null;
    }
}
