package com.tariff.tariff_backend.model.tariffs_new;

import java.math.BigDecimal;

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
@Table(name = "tariff_new", schema = "tariffs")
public class Tariff {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "tariffid")
    private Integer tariffId;

    @Column (name = "descriptionwcountry", nullable = false)
    private String descriptionwcountry;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn (name = "partnercountry", nullable = false)
    @com.fasterxml.jackson.annotation.JsonIgnore 
    private Country partnerCountry;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn (name = "reportercountry", nullable = false)
    @com.fasterxml.jackson.annotation.JsonIgnore 
    private Country reporterCountry;

    @Column (nullable = false)
    private String unitname;

    @Column (nullable = false)
    private String category;

    @Column (name = "advalorem")
    private BigDecimal adValorem;
    
    @Column (name = "specificperunit")
    private BigDecimal specificPerUnit;

}
