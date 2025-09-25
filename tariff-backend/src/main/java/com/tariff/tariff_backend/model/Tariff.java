package com.tariff.tariff_backend.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@NoArgsConstructor
@AllArgsConstructor // auto generate constructors
@Data // auto generates getter,setters,toString etc so udn to write out
@Entity // tells springboot that this class is an entity in our DB
@Table(name="tariff_new", schema = "tariffs") // where to look for the entity
@Builder


public class Tariff {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "tariffid")
    private Integer tariffid;

    @Column(name = "descriptionwcountry")
    private String descriptionwcountry;

    @Column(name = "partnercountry")
    private Integer partnercountry;

    @Column(name = "reportercountry")
    private Integer reportercountry;

    @Column(name = "unitname")
    private String unitname;

    @Column(name = "category")
    private String category;

    @Column(name = "advalorem")
    private java.math.BigDecimal advalorem;

    @Column(name = "specificperunit")
    private java.math.BigDecimal specificperunit;
}