package com.tariff.tariff_backend.model.tariffs_new;

import java.math.BigDecimal;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "Calculated_Result", schema = "tariffs")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class CalculatedResult {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer calculatedID;

    @Column(nullable = false, precision = 10, scale = 2)
    private BigDecimal value;
}
