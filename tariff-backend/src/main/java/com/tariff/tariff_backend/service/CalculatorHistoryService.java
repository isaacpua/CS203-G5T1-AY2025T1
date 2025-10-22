package com.tariff.tariff_backend.service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.Optional;

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

    public Map<String,Object> editOwn(Integer id, Map<String, Object> snapshotJson, Authentication auth){
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

        Optional<TransactionLine> txCheck = txRepo.findByTransactionIdAndUserId(id,user.getId());
        TransactionLine tx = null;
        if (txCheck.isPresent()) {
            tx = txCheck.get();
        }
        formatNumbers(snapshotJson, "total", "quantity", "tariffId", "adValorem", "customsValue", "specificPerUnit");
        tx.setSnapshot(snapshotJson);
        txRepo.save(tx);
        return tx.getSnapshot();

    }

    private void formatNumbers(Map<String, Object> snapshot, String... keys) { //convert string to int/double
        for (String key : keys) {

            // skip if the key is missing or null
            if (!snapshot.containsKey(key) || snapshot.get(key) == null)
                continue;

            Object value = snapshot.get(key);

            // already a number? skip
            if (value instanceof Number)
                continue;

            // try to convert string → number
            if (value instanceof String str && !str.isBlank()) {
                try {
                    // if the string has a decimal point, treat as Double; else Long
                    Number numericValue = str.contains(".")
                            ? Double.parseDouble(str)
                            : Integer.parseInt(str);

                    snapshot.put(key, numericValue);
                } catch (NumberFormatException e) {
                    // if it's not a valid number, just leave it as-is
                    System.out.println("Skipping non-numeric value for key: " + key);
                }
            }
        }
    }

}
