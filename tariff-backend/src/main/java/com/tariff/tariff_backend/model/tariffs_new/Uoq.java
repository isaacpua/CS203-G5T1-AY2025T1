package com.tariff.tariff_backend.model.tariffs_new;

import java.math.BigDecimal;
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

@Entity
@Table(name = "UOQ", schema = "tariffs")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Uoq {
    @Id 
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer unitID;

    @Column(nullable = false)
    private String name;

    @Column()
    private BigDecimal calcStep;

    @Column(nullable = false)
    private String category;

    @Column()
    private BigDecimal adValorem;

    @Column()
    private BigDecimal specificPerUnit;

    @JsonIgnore
    @OneToMany(mappedBy = "unit", fetch = FetchType.LAZY) //can get tariffs from uoq
    private List<Tariff> tariffs = new ArrayList<>();

    public void addTariff(Tariff t) {
        tariffs.add(t);
        t.setUnit(this);
    }

}
