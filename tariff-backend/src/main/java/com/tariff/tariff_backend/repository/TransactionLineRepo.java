package com.tariff.tariff_backend.repository;

import com.tariff.tariff_backend.model.tariffs_new.TransactionLine;
import com.tariff.tariff_backend.model.User;
import com.tariff.tariff_backend.model.tariffs_new.Tariff;
import org.springframework.data.jpa.repository.JpaRepository;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

public interface TransactionLineRepo extends JpaRepository<TransactionLine, Integer> {

    Optional<TransactionLine> findByTransactionId(Integer transactionId);

    List<TransactionLine> findByUser(User user);

    List<TransactionLine> findByTariff(Tariff tariff);

    List<TransactionLine> findByCalculatedValue(BigDecimal calculatedValue);

    // Range queries
    List<TransactionLine> findByCalculatedValueGreaterThan(BigDecimal minValue);

    List<TransactionLine> findByCalculatedValueBetween(BigDecimal minValue, BigDecimal maxValue);
}
