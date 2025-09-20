package com.tariff.tariff_backend.model.tariffs_new;

import java.util.ArrayList;
import java.util.List;

import com.fasterxml.jackson.annotation.JsonIgnore;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data //auto setter getter
@NoArgsConstructor
@AllArgsConstructor // constructor with all fields
@Entity
@Table(name = "Country", schema = "tariffs")
public class Country {
    @Id 
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer countryID;

    @Column(nullable = false, unique = true)
    private String iso2;

    @Column(nullable = false)
    private String name;

    @JsonIgnore //get partnercountry
    @OneToMany(mappedBy = "partnerCountry", fetch = FetchType.LAZY)
    private List<Tariff> partnerTariffs = new ArrayList<>();

    @JsonIgnore //get reportercountry
    @OneToMany(mappedBy = "reporterCountry", fetch = FetchType.LAZY)
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
