package com.tariff.tariff_backend.service;

import com.tariff.tariff_backend.dto.CalculateDutyRequest;
import com.tariff.tariff_backend.dto.CalculateDutyResponse;
import com.tariff.tariff_backend.repository.TariffNewRepo;
import com.tariff.tariff_backend.repository.TransactionLineRepo;
import com.tariff.tariff_backend.repository.UserRepo;

public class CalculationService {
    
    private final TariffNewRepo tariffRepo;
    private final TransactionLineRepo txRepo;
    private final UserRepo userRepo;

    public CalculationService(TariffNewRepo tariffRepo, TransactionLineRepo txRepo, UserRepo userRepo){
        this.tariffRepo = tariffRepo;
        this.txRepo = txRepo;
        this.userRepo = userRepo;
    }

    public CalculateDutyResponse calculateAndStore(CalculateDutyRequest request){
        if (request.tariffId() == null){
            throw new IllegalArgumentException("tariffID is needed");
        }
        if (request.customsValue() == null && request.quantity() == null){
            throw new IllegalArgumentException("Provide a Value and/or quantity");
        }
        
    }
}
