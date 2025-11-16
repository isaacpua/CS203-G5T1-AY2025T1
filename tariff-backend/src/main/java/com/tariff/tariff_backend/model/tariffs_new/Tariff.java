package com.tariff.tariff_backend.model.tariffs_new;

import java.math.BigDecimal;
import java.time.LocalDate;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;

import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "tariff_master", schema = "tariffs")
@Schema(description = "Tariff entity representing trade tariff information")
public class Tariff {

    @Id
    @Column(name = "tariffid")
    @Schema(description = "Unique tariff identifier", example = "12345")
    private String tariffId;

    @Column (name = "descriptionwcountry", nullable = false)
    @Schema(description = "Product description with country context", example = "Live horses - from Canada", required = true)
    private String descriptionwcountry;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn (name = "partnercountry", nullable = false)
    @com.fasterxml.jackson.annotation.JsonIgnore
    @Schema(description = "Partner/source country", required = true)
    private Country partnerCountry;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn (name = "reportercountry", nullable = false)
    @com.fasterxml.jackson.annotation.JsonIgnore
    @Schema(description = "Reporter/destination country", required = true)
    private Country reporterCountry;

    @Column (nullable = false)
    @Schema(description = "Unit of measurement", example = "kg", required = true)
    private String unitname;

    @Column (nullable = false)
    @Schema(description = "Product category", example = "Live Animals", required = true)
    private String category;

    @Column (name = "advalorem", precision = 38, scale = 6)
    @Schema(description = "Ad valorem tariff rate (percentage)", example = "12.5")
    private BigDecimal adValorem;
    
    @Column (name = "specificperunit", precision = 38, scale = 6)
    @Schema(description = "Specific tariff rate per unit", example = "0.75")
    private BigDecimal specificPerUnit;

    @Column(name = "effectivedate") 
    @Schema(description = "Date when the tariff becomes effective", example = "2024-01-01")
    private LocalDate effectivedate;

    @Column(name = "expirydate") 
    @Schema(description = "Date when the tariff expires", example = "2024-12-31")
    private LocalDate expirydate;

    @Column(name = "datasource")
    @Schema(description = "Source of the tariff data", example = "Government Gazette")
    private String datasource;

    @Column(name = "year")
    @Schema(description = "year sourced for the tariff data", example = "2002")
    private Integer year;
}
