package com.tariff.tariff_backend.repository;

import com.tariff.tariff_backend.model.tariffs_new.TransactionLine;
import com.tariff.tariff_backend.model.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface TransactionLineRepo extends JpaRepository<TransactionLine, Integer> {

    Optional<TransactionLine> findByTransactionId(Integer transactionId);

    List<TransactionLine> findByUser(User user);

}
