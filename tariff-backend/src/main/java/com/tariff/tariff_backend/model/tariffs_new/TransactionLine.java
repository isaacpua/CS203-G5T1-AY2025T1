package com.tariff.tariff_backend.model.tariffs_new;

import java.math.BigDecimal;

import com.tariff.tariff_backend.model.User;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data //auto setter getter
@NoArgsConstructor
@AllArgsConstructor // constructor with all fields
@Entity
@Table(name = "transaction_line", schema = "tariffs")
public class TransactionLine {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "transactionid")
    private Integer transactionId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "userid", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "tariffid", nullable = false)
    private Tariff tariff;

    @Column(name = "value", nullable = false)
    private BigDecimal calculatedValue;
}
