package com.tariff.tariff_backend.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@NoArgsConstructor
@AllArgsConstructor // auto generate constructors
@Data // auto generates getter,setters,toString etc
@Entity // tells springboot that this class is an entity in our DB
@Table(name="tariff", schema = "tariffs") // where to look for the entity

public class Tariff {
    @Id // next variable is primary key
    private Integer id;
    private Integer hts8;
    private String brief_description;
    private String mfn_text_rate;
}
