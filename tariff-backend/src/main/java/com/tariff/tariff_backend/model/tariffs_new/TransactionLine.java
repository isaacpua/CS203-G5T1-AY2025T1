package com.tariff.tariff_backend.model.tariffs_new;

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

@Entity
@Table(name = "TransactionLine", schema = "tariffs")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class TransactionLine {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer transactionID;

    @Column(nullable = false)
    private Integer userID;

    // --- Relationships ---
    @ManyToOne(optional = false, fetch = FetchType.LAZY)
    @JoinColumn(name = "tariffID")
    private Tariff tariff;

    @ManyToOne(optional = false, fetch = FetchType.LAZY)
    @JoinColumn(name = "calculatedID")
    private CalculatedResult calculated;
}
