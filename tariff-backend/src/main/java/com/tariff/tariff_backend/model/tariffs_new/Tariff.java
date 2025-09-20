package com.tariff.tariff_backend.model.tariffs_new;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor // constructor with all fields
@Entity
@Table(name = "Tariffs", schema = "tariffs")
public class Tariff {
    @Id 
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer tariffID;

    @Column(nullable = false, columnDefinition = "text")
    private String descriptionWCountry;

    @ManyToOne(optional = false)
    @JoinColumn(name = "partnerCountry")
    private Country partnerCountry;

    @ManyToOne(optional = false)
    @JoinColumn(name = "reporterCountry")
    private Country reporterCountry;

    @ManyToOne(optional = false)
    @JoinColumn(name = "unitID")
    private Uoq unit;
}
