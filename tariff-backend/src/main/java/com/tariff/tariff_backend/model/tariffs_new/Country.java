package com.tariff.tariff_backend.model.tariffs_new;

import java.util.ArrayList;
import java.util.List;
import com.fasterxml.jackson.annotation.JsonIgnore;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "country", schema = "tariffs")
@Schema(description = "Country entity representing trading nations")
public class Country {
    
    @Id 
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Schema(description = "Unique country identifier", example = "840")
    private Integer countryId;

    @Column(nullable = false, unique = true)
    @Schema(description = "ISO 2-letter country code", example = "US", required = true)
    private String iso2;

    @Column(nullable = false)
    @Schema(description = "Full country name", example = "United States", required = true)
    private String name;

    @JsonIgnore 
    @OneToMany(mappedBy = "partnerCountry", fetch = FetchType.LAZY)
    @Schema(hidden = true)
    private List<Tariff> partnerTariffs = new ArrayList<>();

    @JsonIgnore 
    @OneToMany(mappedBy = "reporterCountry", fetch = FetchType.LAZY)
    @Schema(hidden = true)
    private List<Tariff> reporterTariffs = new ArrayList<>();

    public void addPartnerTariff(Tariff t) {
        partnerTariffs.add(t);
        t.setPartnerCountry(this);
    }
    public void addReporterTariff(Tariff t) {
        reporterTariffs.add(t);
        t.setReporterCountry(this);
    }
}
