package com.tariff.tariff_backend.model.tariffs;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@NoArgsConstructor
@AllArgsConstructor // auto generate constructors
@Data // auto generates getter,setters,toString etc so udn to write out
@Entity // tells springboot that this class is an entity in our DB
@Table(name="tariff", schema = "tariffs") // where to look for the entity

public class Tariff {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) //ID is the primary key, generated value just helps to keep track that if u add one in it increments auto
    private Integer id;
    @Column (unique = true, nullable = false) //its a column with unique hts8 and cannot be null
    private Integer hts8;
    @Column (name = "brief_description", nullable = false)
    private String briefDescription;
    @Column (name = "mfn_text_rate", nullable = false)
    private String mfnTextRate;
}
