package com.tariff.tariff_backend.service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;

import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import com.tariff.tariff_backend.dto.CalculationDTO.TransactionLineDTO;
import com.tariff.tariff_backend.model.User;
import com.tariff.tariff_backend.model.tariffs_new.TransactionLine;
import com.tariff.tariff_backend.repository.TransactionLineRepo;
import com.tariff.tariff_backend.repository.UserRepo;

@Service

public class CalculatorHistoryService {

    private final TransactionLineRepo txRepo;
    private final UserRepo userRepo;

    public CalculatorHistoryService(TransactionLineRepo txRepo, UserRepo userRepo) {
        this.txRepo = txRepo;
        this.userRepo = userRepo;
    }

    public List<TransactionLineDTO> viewHistory() {
        List<TransactionLineDTO> result = new ArrayList<>();
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        String username = null;
        if (auth != null) {
            username = auth.getName();
        }
        if (username == null) {
            throw new IllegalArgumentException("No authenticated user");
        }

        User user = null; // getting user
        try {
            user = userRepo.findByUsername(username).get();
        } catch (NoSuchElementException e) {
            throw new IllegalArgumentException("User not found: " + username);
        }
        List<TransactionLine> transactionLines = txRepo.findByUser(user);

        for (TransactionLine tx : transactionLines){
            Map<String, Object> snap = tx.getSnapshot();
            result.add(new TransactionLineDTO(tx.getTransactionId(), tx.getCreated_at(), snap));
        }

        return result;
    }

    public void deleteOwn(Integer id, Authentication auth){
        String username = null;

        if (auth != null) {
            username = auth.getName();
        }
        if (username == null) {
            throw new IllegalArgumentException("No authenticated user");
        }

        User user = null; // getting user
        try {
            user = userRepo.findByUsername(username).get();
        } catch (NoSuchElementException e) {
            throw new IllegalArgumentException("User not found: " + username);
        }
        long rows = txRepo.deleteByTransactionIdAndUserId(id, user.getId());
        if (rows == 0) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Transaction not found");
        }
    }
}
